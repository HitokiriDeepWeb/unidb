from dataclasses import asdict
from pathlib import Path

import asyncpg
import pytest

from application.services import (
    DatabaseFileCopier,
    UniprotDatabaseSetup,
    UniprotOperator,
)
from core.config import UniprotFiles
from infrastructure.database.postgresql import (
    ConnectionConfig,
    ConnectionPoolConfig,
    PostgreSQLAdapter,
    PostgreSQLUniprotLifecycle,
    get_available_connections_amount,
    setup_connection_pool_config,
    setup_queue_config,
)
from infrastructure.preparation.prepare_files import (
    FilePreparer,
    UpdateChecker,
)
from infrastructure.preparation.prepare_files.download import Downloader
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
from tests.integration.conftest import DATABASE_ENV


async def _compose_dependencies(
    path_to_files: Path,
) -> tuple[UniprotDatabaseSetup, int, ConnectionConfig]:
    trgm_required = True
    uniprot_lifecycle = PostgreSQLUniprotLifecycle(trgm_required=trgm_required)
    postgresql_copy_adapter = PostgreSQLAdapter()
    file_preparer = FilePreparer(
        source_folder=path_to_files, preparation_is_required=False
    )

    single_connection_config = _get_connection_config()
    available_connections = await get_available_connections_amount(
        asdict(single_connection_config)
    )
    workers_number = 8
    connection_pool_config: ConnectionPoolConfig = setup_connection_pool_config(
        **asdict(single_connection_config),
        workers_number=workers_number,
        available_connections=available_connections,
    )
    db_copier = _get_database_file_copier(
        path_to_files=path_to_files,
        workers_number=workers_number,
        available_connections=available_connections,
        postgresql_copy_adapter=postgresql_copy_adapter,
        connection_pool_config=connection_pool_config,
    )
    uniprot_operator = UniprotOperator(
        uniprot_lifecycle=uniprot_lifecycle, db_connector=postgresql_copy_adapter
    )
    update_checker = UpdateChecker()
    downloader = Downloader()
    system_preparer_config = SystemPreparerConfig(
        download_is_required=False, trgm_required=True, accept_setup_automatically=True
    )
    system_preparer = SystemPreparer(system_preparer_config)
    uniprot_setup = UniprotDatabaseSetup(
        uniprot_operator=uniprot_operator,
        file_preparer=file_preparer,
        db_copier=db_copier,
        system_preparer=system_preparer,
        db_pool_config=asdict(connection_pool_config),
        downloader=downloader,
        update_checker=update_checker,
    )
    return uniprot_setup, workers_number, single_connection_config


def _get_connection_config() -> ConnectionConfig:
    return ConnectionConfig(
        host=DATABASE_ENV.host,
        database=DATABASE_ENV.dbname,
        password=DATABASE_ENV.password,
        port=DATABASE_ENV.port,
        user=DATABASE_ENV.user,
    )


def _get_database_file_copier(
    path_to_files: Path,
    workers_number: int,
    available_connections: int,
    postgresql_copy_adapter: PostgreSQLAdapter,
    connection_pool_config: ConnectionPoolConfig,
) -> DatabaseFileCopier:
    iterators_to_tables = stick_iterators_to_tables(path_to_files)
    queue_config = setup_queue_config(workers_number, available_connections)

    trembl_workers_number = calculate_workers_to_split_trembl_file(workers_number)
    trembl_path = path_to_files / UniprotFiles.TREMBL
    chunk_range_iterator = ChunkRangeIterator(
        path_to_file=trembl_path,
        workers_number=trembl_workers_number,
    )
    trembl_iterator = create_trembl_iterator_partial(path_to_files)
    return DatabaseFileCopier(
        db_adapter=postgresql_copy_adapter,
        queue_config=queue_config,
        connection_pool_config=asdict(connection_pool_config),
        trembl_iterator=trembl_iterator,  # type: ignore
        chunk_range_iterator=chunk_range_iterator,
        iterators_to_tables=iterators_to_tables,
    )


@pytest.mark.asyncio
async def test_postgresql_uniprot_setup(tmp_path: Path):
    # Arrange.
    (
        uniprot_setup,
        workers_number,
        single_connection_config,
    ) = await _compose_dependencies(tmp_path)

    query = """
            SELECT u.accession
            FROM uniprot_kb u
            JOIN taxonomy t ON u.ncbi_organism_id = t.ncbi_taxon_id
            WHERE ncbi_taxon_id = 9606
            AND u.source = 'sp'
            AND u.sequence like '%KHL%'
            """
    expected_result = [dict(accession="A0JNW5"), dict(accession="A1A519")]

    # Act.
    await uniprot_setup.setup(workers_number=workers_number, download_is_required=False)

    conn = await asyncpg.connect(**asdict(single_connection_config))
    rows = await conn.fetch(query)
    result: list[dict[str, str]] = [dict(row) for row in rows]

    await conn.close()

    # Assert.
    assert result == expected_result
