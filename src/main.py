"""
This software downloads and creates a database based on data from UniProt and NCBI.

UniProt data is licensed under the Creative Commons Attribution 4.0
International (CC BY 4.0) License.
Full license text: https://creativecommons.org/licenses/by/4.0/
Source: https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/LICENSE

All data on NCBI FTP site is public, non-sensitive,
unrestricted scientific data sharing among scientific communities.
Source: https://ftp.ncbi.nih.gov/pub/README.ftp
"""

import asyncio
from dataclasses import asdict
from pathlib import Path

from core.logging_config import setup_logging
from infrastructure.ui.cli import app_args, log_config

logger = setup_logging(
    log_config.log_path,
    log_config.log_level,
    log_config.log_type,
    log_config.verbose,
)

# ruff: noqa: E402
from application.services import (
    DatabaseFileCopier,
    UniprotDatabaseSetup,
    UniprotOperator,
)
from application.services.exceptions import NoUpdateRequired
from core.config import UniprotFiles
from domain.entities import DEFAULT_SOURCE_FILES_FOLDER
from infrastructure.database.postgresql import (
    ConnectionConfig,
    ConnectionPoolConfig,
    PostgreSQLAdapter,
    PostgreSQLUniprotLifecycle,
    adjust_workers_by_db_connection_limit,
    get_available_connections_amount,
    setup_connection_pool_config,
    setup_queue_config,
)
from infrastructure.preparation.prepare_files import (
    FilePreparer,
    UpdateChecker,
)
from infrastructure.preparation.prepare_files.download import (
    Downloader,
)
from infrastructure.preparation.prepare_system import (
    SystemPreparer,
    SystemPreparerConfig,
)
from infrastructure.process_data import (
    calculate_workers_to_split_trembl_file,
    create_trembl_iterator_partial,
    stick_iterators_to_tables,
)
from infrastructure.process_data.uniprot.fasta import ChunkRangeIterator

path_to_source_files: Path | None = app_args.path_to_source_files
path_to_source_archives: Path | None = app_args.path_to_source_archives
no_clean_up: bool = app_args.no_clean_up_on_failure

files_were_downloaded: bool = False
archives_were_downloaded: bool = False
download_is_required: bool = True
preparation_is_required: bool = True

if path_to_source_files is not None:
    source_folder = path_to_source_files
    files_were_downloaded = True
    download_is_required = False
    preparation_is_required = False

elif path_to_source_archives is not None:
    source_folder = path_to_source_archives
    archives_were_downloaded = True
    download_is_required = False

else:
    source_folder = DEFAULT_SOURCE_FILES_FOLDER


async def main() -> None:
    hello()
    await setup_uniprot_database()


def hello() -> None:
    """Introduction message."""
    logger.info(
        "This util will download all necessary files "
        "and set up / update uniprot database"
    )


async def setup_uniprot_database() -> None:
    """Download (if needed) and install UniProt database."""
    uniprot_setup, workers_number = await _compose_dependencies()

    try:
        await uniprot_setup.setup(
            workers_number=workers_number,
            download_is_required=download_is_required,
        )
        logger.info("UniProt database has been set up successfully.")

    except NoUpdateRequired:
        return

    except Exception:
        logger.exception("Could not set up UniProt database")
        await _clean_up(uniprot_setup)
        raise SystemExit(1) from None


async def _clean_up(uniprot_setup: UniprotDatabaseSetup) -> None:
    if not no_clean_up:
        await uniprot_setup.remove_on_failure(files_were_downloaded)
        logger.info("Removing database and downloaded files")


async def _compose_dependencies():
    connection_config = _get_connection_config()
    available_connections = await get_available_connections_amount(
        asdict(connection_config)
    )

    workers_number = adjust_workers_by_db_connection_limit(
        desired_workers_number=app_args.processes,
        available_connections=available_connections,
    )

    connection_pool_config = _get_connection_pool_config(
        workers_number=workers_number,
        available_connections=available_connections,
    )

    trgm_required = app_args.trgm

    postgresql_adapter = PostgreSQLAdapter()
    uniprot_lifecycle = PostgreSQLUniprotLifecycle(trgm_required=trgm_required)
    uniprot_operator = UniprotOperator(
        db_connector=postgresql_adapter, uniprot_lifecycle=uniprot_lifecycle
    )

    db_copier = _get_database_file_copier(
        workers_number=workers_number,
        available_connections=available_connections,
        postgresql_adapter=postgresql_adapter,
        connection_pool_config=connection_pool_config,
    )

    system_preparer_config = SystemPreparerConfig(
        download_is_required=download_is_required,
        trgm_required=trgm_required,
        accept_setup_automatically=app_args.y,
    )
    system_preparer = SystemPreparer(system_preparer_config)
    downloader = Downloader()
    update_checker = UpdateChecker()
    file_preparer = FilePreparer(
        source_folder=source_folder, preparation_is_required=preparation_is_required
    )

    uniprot_setup = UniprotDatabaseSetup(
        uniprot_operator=uniprot_operator,
        update_checker=update_checker,
        db_pool_config=asdict(connection_pool_config),
        file_preparer=file_preparer,
        db_copier=db_copier,
        system_preparer=system_preparer,
        downloader=downloader,
    )

    return uniprot_setup, workers_number


def _get_connection_config() -> ConnectionConfig:
    return ConnectionConfig(
        database=app_args.dbname,
        user=app_args.dbuser,
        port=app_args.port,
        host=app_args.host,
        password=app_args.password,
    )


def _get_connection_pool_config(
    workers_number: int, available_connections: int
) -> ConnectionPoolConfig:
    return setup_connection_pool_config(
        database=app_args.dbname,
        user=app_args.dbuser,
        port=app_args.port,
        host=app_args.host,
        password=app_args.password,
        workers_number=workers_number,
        available_connections=available_connections,
    )


def _get_database_file_copier(
    workers_number: int,
    available_connections: int,
    connection_pool_config: ConnectionPoolConfig,
    postgresql_adapter: PostgreSQLAdapter,
) -> DatabaseFileCopier:
    trembl_workers_number = calculate_workers_to_split_trembl_file(workers_number)
    path_to_trembl = source_folder / UniprotFiles.TREMBL

    chunk_range_iterator = ChunkRangeIterator(
        path_to_file=path_to_trembl,
        workers_number=trembl_workers_number,
    )
    trembl_iterator = create_trembl_iterator_partial(source_folder)
    queue_config = setup_queue_config(workers_number, available_connections)
    iterators_to_tables = stick_iterators_to_tables(source_folder)

    db_copier = DatabaseFileCopier(
        db_adapter=postgresql_adapter,
        queue_config=queue_config,
        connection_pool_config=asdict(connection_pool_config),
        trembl_iterator=trembl_iterator,  # type: ignore
        chunk_range_iterator=chunk_range_iterator,
        iterators_to_tables=iterators_to_tables,
    )
    return db_copier


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("User terminated program manually")
