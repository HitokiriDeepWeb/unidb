import asyncio
import contextlib
from collections.abc import Coroutine
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

from application.interfaces import (
    DownloaderProtocol,
    FilePreparerProtocol,
    SystemPreparerProtocol,
    UpdateCheckerProtocol,
)
from application.services.copy_files import DatabaseFileCopier
from application.services.exceptions import NoUpdateRequired, UniprotSetupError
from application.services.uniprot_operator import UniprotOperator
from core.interfaces import StringKeyMapping
from core.utils import create_tasks, init_shutdown_event, process_tasks


class SetupUniprotDatabase:
    def __init__(
        self,
        uniprot_operator: UniprotOperator,
        db_copier: DatabaseFileCopier,
        db_pool_config: StringKeyMapping,
        file_preparer: FilePreparerProtocol,
        system_preparer: SystemPreparerProtocol,
        downloader: DownloaderProtocol,
        update_checker: UpdateCheckerProtocol,
    ):
        self._uniprot_operator = uniprot_operator
        self._db_copier = db_copier
        self._db_pool_config = db_pool_config
        self._file_preparer = file_preparer
        self._system_preparer = system_preparer
        self._downloader = downloader
        self._update_checker = update_checker

    async def remove_on_failure(self, files_were_downloaded: bool) -> None:
        """Remove database and source files after unsuccessful setup attempt."""
        coros: list[Coroutine] = [
            self._uniprot_operator.remove_database(self._db_pool_config)
        ]

        if not files_were_downloaded:
            coros.append(self._system_preparer.delete_unnecessary_files())

        tasks = create_tasks(coros)
        await process_tasks(tasks)

    async def setup(
        self,
        workers_number: int,
        download_is_required: bool = True,
    ) -> None:
        """Orchestrate UniProt database setup."""
        try:
            await self._prepare(download_is_required)
            await self._copy_data(workers_number, download_is_required)
            await self._uniprot_operator.finalize_database_setup(self._db_pool_config)

            self._update_checker.save_database_update_time()

        except NoUpdateRequired:
            raise

        except Exception as e:
            raise UniprotSetupError from e

    async def _prepare(self, download_is_required: bool) -> None:
        """Execute database reset and then preparation queries."""
        if not download_is_required:
            await self._prepare_without_download()

        elif await self._update_checker.need_update():
            await self._prepare_with_download()

    @staticmethod
    def _download_is_not_required(
        files_were_downloaded: bool, archives_were_downloaded: bool
    ):
        return files_were_downloaded or archives_were_downloaded

    async def _prepare_without_download(self):
        with contextlib.suppress(Exception):
            await self._uniprot_operator.reset_database(self._db_pool_config)

        await self._system_preparer.prepare_environment()
        await self._uniprot_operator.prepare_database_environment(self._db_pool_config)

    async def _prepare_with_download(self):
        with contextlib.suppress(Exception):
            await self._uniprot_operator.reset_database(self._db_pool_config)

        await self._system_preparer.prepare_environment()
        await self._downloader.download_files()
        await self._uniprot_operator.prepare_database_environment(self._db_pool_config)

    async def _copy_data(
        self,
        workers_number: int,
        download_is_required: bool,
    ) -> None:
        """
        Copy data from required files to database in parallel processes
        and then delete used files.
        """
        await self._copy_data_in_separate_processes(workers_number)

        if download_is_required:
            await self._system_preparer.delete_unnecessary_files()

    async def _copy_data_in_separate_processes(self, workers_number: int) -> None:
        with Manager() as manager:
            event = manager.Event()

            with ProcessPoolExecutor(
                max_workers=workers_number,
                initializer=init_shutdown_event,
                initargs=(event,),
            ) as process_pool:
                loop = asyncio.get_running_loop()

                await self._file_preparer.prepare_required_files(
                    loop=loop, process_pool=process_pool, event=event
                )

                await self._db_copier.copy(
                    loop=loop,
                    process_pool=process_pool,
                    event=event,
                )
