import asyncio
from asyncio import Semaphore, Task
from collections.abc import Coroutine
from itertools import chain
from pathlib import Path
from typing import TypedDict

from aiohttp import ClientSession

from core.config import (
    GRACEFUL_SHUTDOWN_DELAY,
    HEAD_REQUEST_TIMEOUT,
    LARGE_FILE_TIMEOUT,
    NCBI_LINK,
    SEMAPHORE,
    SMALL_FILE_TIMEOUT,
    UNIPROT_LARGE_FILES_CONNECTIONS,
    UNIPROT_SP_ISOFORMS_LINK,
    UNIPROT_SP_LINK,
    UNIPROT_TR_LINK,
)
from core.utils import create_tasks, process_tasks
from domain.entities import DEFAULT_SOURCE_FILES_FOLDER
from infrastructure.preparation.common_types import Link
from infrastructure.preparation.prepare_files.download.download_files import (
    FullFileDownloader,
    PartOfFileDownloader,
)
from infrastructure.preparation.prepare_files.download.file_chunker import (
    FileChunkCalculator,
)
from infrastructure.preparation.prepare_files.download.get_file_size import (
    get_file_size,
)


class DownloadArgs(TypedDict):
    url: Link
    path_to_save: Path


class Downloader:
    def __init__(self):
        self._large_file_timeout = LARGE_FILE_TIMEOUT
        self._graceful_shutdown_delay = GRACEFUL_SHUTDOWN_DELAY
        self._uniprot_large_files_connections = UNIPROT_LARGE_FILES_CONNECTIONS
        self._small_file_timeout = SMALL_FILE_TIMEOUT
        self._head_request_timeout = HEAD_REQUEST_TIMEOUT
        self._semaphore = SEMAPHORE
        self._ncbi_link = NCBI_LINK
        self._uniprot_sp_isoforms_link = UNIPROT_SP_ISOFORMS_LINK
        self._uniprot_sp_link = UNIPROT_SP_LINK
        self._uniprot_tr_link = UNIPROT_TR_LINK

    async def download_files(self) -> None:
        main_timeout = self._large_file_timeout

        async with ClientSession(
            timeout=main_timeout, raise_for_status=True
        ) as session:
            full_tasks = self._get_full_file_download_tasks(session)
            part_tasks = await self._get_trembl_file_parts_download_tasks(session)

            tasks: list[Task] = list(chain(full_tasks, part_tasks))
            await process_tasks(tasks)

        # For graceful shutdown of connections with SSL.
        await asyncio.sleep(self._graceful_shutdown_delay)

    def _get_full_file_download_tasks(self, session: ClientSession) -> list[Task]:
        download_args: list[DownloadArgs] = [
            DownloadArgs(
                url=self._uniprot_sp_link, path_to_save=DEFAULT_SOURCE_FILES_FOLDER
            ),
            DownloadArgs(
                url=self._uniprot_sp_isoforms_link,
                path_to_save=DEFAULT_SOURCE_FILES_FOLDER,
            ),
            DownloadArgs(url=self._ncbi_link, path_to_save=DEFAULT_SOURCE_FILES_FOLDER),
        ]

        downloaders: list[FullFileDownloader] = [
            FullFileDownloader(
                session=session,
                url=kwargs["url"],
                path_to_save=kwargs["path_to_save"],
                semaphore=self._semaphore,
            )
            for kwargs in download_args
        ]

        regular_file_timeout = self._small_file_timeout
        coroutines: list[Coroutine] = [
            downloader.download_file(timeout=regular_file_timeout)
            for downloader in downloaders
        ]

        tasks = create_tasks(coroutines)
        return tasks

    async def _get_trembl_file_parts_download_tasks(self, session: ClientSession):
        """Download file with TrEMBL sequences in separate parts."""
        timeout = self._head_request_timeout

        file_size = await get_file_size(
            url=self._uniprot_tr_link, session=session, timeout=timeout
        )

        tasks = self._get_tasks_that_partially_download_file(
            session=session,
            file_parts_quantity=self._uniprot_large_files_connections,
            file_size=file_size,
            url=self._uniprot_tr_link,
            path_to_save=DEFAULT_SOURCE_FILES_FOLDER,
            semaphore=self._semaphore,
        )
        return tasks

    def _get_tasks_that_partially_download_file(
        self,
        session: ClientSession,
        file_parts_quantity: int,
        file_size: int,
        url: Link,
        path_to_save: Path,
        semaphore: Semaphore,
    ) -> list[Task]:
        """Append all tasks that download part of the file to task list."""
        file_chunker = FileChunkCalculator(file_size, file_parts_quantity)
        tasks: list[Task] = []

        for file_part in range(file_parts_quantity):
            part_downloader = PartOfFileDownloader(
                session=session,
                url=url,
                file_part_number=file_part,
                path_to_save=path_to_save,
                semaphore=semaphore,
                file_chunker=file_chunker,
            )

            tasks.append(
                asyncio.create_task(
                    part_downloader.download_file(self._large_file_timeout)
                )
            )

        return tasks
