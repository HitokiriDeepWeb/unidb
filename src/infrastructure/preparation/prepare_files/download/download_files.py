import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from domain.models import ChunkRange
from infrastructure.preparation.common_types import Link
from infrastructure.preparation.prepare_files.download.config import DownloadConfig
from infrastructure.preparation.prepare_files.download.file_chunker import (
    FileChunkCalculator,
)

logger = logging.getLogger(__name__)


class FileDownloader:
    def __init__(
        self,
        session: ClientSession,
        url: Link,
        config: DownloadConfig,
    ):
        self._session = session
        self._url = url
        self._config = config

    def extract_file_name_from_url(self) -> str:
        return Path(urlparse(self._url).path).name

    def set_file_path(self, path_to_save: Path, file_name: str) -> Path:
        path_to_file = path_to_save / file_name
        return path_to_file

    async def execute_http_download(
        self,
        path_to_file: Path,
        timeout: ClientTimeout,
        headers: dict[str, str] | None = None,
    ) -> None:
        file_name = self.extract_file_name_from_url()

        try:
            await self._try_execute_http_download(path_to_file, timeout, headers)

        except asyncio.TimeoutError:
            logger.exception("Unable to download %s, check your connection", file_name)
            raise

        except Exception:
            logger.exception("Unable to download %s", file_name)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def _try_execute_http_download(
        self,
        path_to_file: Path,
        timeout: ClientTimeout,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Download file and write its content to file."""
        async with (
            self._config.SEMAPHORE,
            self._session.get(self._url, headers=headers, timeout=timeout) as resp,
        ):
            await self._write_chunks_to_file(resp, path_to_file)

    async def _write_chunks_to_file(
        self, response: ClientResponse, path_to_file: Path
    ) -> None:
        """Write downloaded content to file piece by piece."""
        async with aiofiles.open(path_to_file, mode="wb") as output_file:
            async for chunk in response.content.iter_chunked(self._config.CHUNK_SIZE):
                await output_file.write(chunk)


class DownloadFullFile:
    """Download regular sized file fully."""

    def __init__(
        self,
        session: ClientSession,
        url: Link,
        path_to_save: Path,
        config: DownloadConfig,
    ):
        self._url = url
        self._path_to_save = path_to_save
        self._file_downloader = FileDownloader(session, url, config)

    async def download_file(self, timeout: ClientTimeout) -> None:
        file_name = self._file_downloader.extract_file_name_from_url()
        path_to_file = self._file_downloader.set_file_path(
            self._path_to_save, file_name
        )
        logger.info("...downloading %s", self._url)

        try:
            await self._file_downloader.execute_http_download(path_to_file, timeout)

        except asyncio.TimeoutError:
            logger.exception(
                "Unable to download %s, connection timed out",
                file_name,
            )
            raise

        except Exception:
            logger.exception("Unable to download %s", file_name)
            raise


class DownloadPartOfFile:
    """Download part of the file."""

    def __init__(
        self,
        session: ClientSession,
        url: Link,
        file_part_number: int,
        path_to_save: Path,
        config: DownloadConfig,
        file_chunker: FileChunkCalculator,
    ):
        self._path_to_save = path_to_save
        self._file_downloader = FileDownloader(session, url, config)
        self._file_part_number = file_part_number
        self._file_chunker = file_chunker

    async def download_file(self, timeout: ClientTimeout) -> None:
        """Make all preparations and download file."""
        file_name = self._file_downloader.extract_file_name_from_url()

        logger.info("...downloading %s", file_name)
        part_file_path, headers = self._setup_download_settings(file_name)

        await self._file_downloader.execute_http_download(
            part_file_path, timeout, headers
        )

    def _setup_download_settings(self, file_name: str) -> tuple[Path, dict[str, str]]:
        try:
            part_file_path, headers = self._try_setup_download_settings(file_name)
            return part_file_path, headers

        except Exception:
            logger.exception("Unable to set up arguments for download %s", file_name)
            raise

    def _try_setup_download_settings(
        self, file_name: str
    ) -> tuple[Path, dict[str, str]]:
        """
        Set appropriate arguments to download file depending on its size
        and file part numbers.
        """
        default_path_to_file = self._file_downloader.set_file_path(
            self._path_to_save, file_name
        )
        part_file_path = self._set_file_path_depending_on_file_part_number(
            default_path_to_file
        )
        headers = self._set_range_header_to_get_file_part()
        return part_file_path, headers

    def _set_file_path_depending_on_file_part_number(
        self, default_path_to_file: Path
    ) -> Path:
        """
        Create numbered file name if it is divided on different parts
        else name it as a whole.
        """
        return Path(f"{default_path_to_file}.{self._file_part_number}")

    def _set_range_header_to_get_file_part(self) -> dict[str, str]:
        """Create header with 'Range' to get part of the file."""
        chunk_range: ChunkRange = self._file_chunker.get_chunk_range(
            self._file_part_number
        )
        return {"Range": f"bytes={chunk_range.start}-{chunk_range.end}"}
