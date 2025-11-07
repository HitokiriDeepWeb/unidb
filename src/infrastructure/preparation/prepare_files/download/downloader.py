import asyncio
from asyncio import Task
from collections.abc import Coroutine
from itertools import chain
from pathlib import Path
from typing import TypedDict

from aiohttp import ClientSession

from core.utils import create_tasks, process_tasks
from domain.entities import DEFAULT_SOURCE_FILES_FOLDER
from infrastructure.preparation.common_types import Link
from infrastructure.preparation.constants import (
    NCBI_LINK,
    UNIPROT_SP_ISOFORMS_LINK,
    UNIPROT_SP_LINK,
    UNIPROT_TR_LINK,
)
from infrastructure.preparation.prepare_files.download.config import (
    DownloadConfig,
)
from infrastructure.preparation.prepare_files.download.download_files import (
    DownloadFullFile,
    DownloadPartOfFile,
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
        self._config = DownloadConfig()

    async def download_files(self) -> None:
        main_timeout = self._config.LARGE_FILE_TIMEOUT

        async with ClientSession(
            timeout=main_timeout, raise_for_status=True
        ) as session:
            full_tasks = self._get_full_file_download_tasks(session)
            part_tasks = await self._get_trembl_file_parts_download_tasks(session)

            tasks: list[Task] = list(chain(full_tasks, part_tasks))
            await process_tasks(tasks)

        # For graceful shutdown of connections with SSL.
        await asyncio.sleep(self._config.GRACEFUL_SHUTDOWN_DELAY)

    def _get_full_file_download_tasks(self, session: ClientSession) -> list[Task]:
        download_args: list[DownloadArgs] = [
            DownloadArgs(url=UNIPROT_SP_LINK, path_to_save=DEFAULT_SOURCE_FILES_FOLDER),
            DownloadArgs(
                url=UNIPROT_SP_ISOFORMS_LINK, path_to_save=DEFAULT_SOURCE_FILES_FOLDER
            ),
            DownloadArgs(url=NCBI_LINK, path_to_save=DEFAULT_SOURCE_FILES_FOLDER),
        ]

        downloaders: list[DownloadFullFile] = [
            DownloadFullFile(
                session, kwargs["url"], kwargs["path_to_save"], self._config
            )
            for kwargs in download_args
        ]

        regular_file_timeout = self._config.SMALL_FILE_TIMEOUT
        coroutines: list[Coroutine] = [
            downloader.download_file(timeout=regular_file_timeout)
            for downloader in downloaders
        ]

        tasks = create_tasks(coroutines)
        return tasks

    async def _get_trembl_file_parts_download_tasks(self, session: ClientSession):
        """Download file with TrEMBL sequences in separate parts."""
        timeout = self._config.HEAD_REQUEST_TIMEOUT

        file_size = await get_file_size(
            url=UNIPROT_TR_LINK, session=session, timeout=timeout
        )

        tasks = self._get_tasks_that_partially_download_file(
            session=session,
            file_parts_quantity=self._config.UNIPROT_LARGE_FILES_CONNECTIONS,
            file_size=file_size,
            url=UNIPROT_TR_LINK,
            path_to_save=DEFAULT_SOURCE_FILES_FOLDER,
            config=self._config,
        )
        return tasks

    def _get_tasks_that_partially_download_file(
        self,
        session: ClientSession,
        file_parts_quantity: int,
        file_size: int,
        url: Link,
        path_to_save: Path,
        config: DownloadConfig,
    ) -> list[Task]:
        """Append all tasks that download part of the file to task list."""
        file_chunker = FileChunkCalculator(file_size, file_parts_quantity)
        tasks: list[Task] = []

        for file_part in range(file_parts_quantity):
            part_downloader = DownloadPartOfFile(
                session=session,
                url=url,
                file_part_number=file_part,
                path_to_save=path_to_save,
                config=config,
                file_chunker=file_chunker,
            )

            tasks.append(
                asyncio.create_task(
                    part_downloader.download_file(self._config.LARGE_FILE_TIMEOUT)
                )
            )

        return tasks
