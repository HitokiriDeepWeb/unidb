import asyncio
import logging
from asyncio import Semaphore
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
from aiohttp import ClientResponse, ClientSession, ClientTimeout
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.common_types import Link
from core.config import CHUNK_SIZE, NETWORK_ERRORS
from domain.models import ChunkRange
from infrastructure.preparation.prepare_files.exceptions import DownloadError

logger = logging.getLogger(__name__)


class FileChunkCalculator:
    """Calculate file chunk ranges for partial download."""

    def __init__(self, file_size: int, total_chunk_quantity: int):
        self._file_size = file_size
        self._total_chunk_quantity = total_chunk_quantity
        self._chunk_size = file_size // total_chunk_quantity

    def get_chunk_range(self, chunk_number: int) -> ChunkRange:
        chunk_start = self._calculate_chunk_start(chunk_number)
        chunk_end = self._calculate_chunk_end(chunk_number, chunk_start)
        return ChunkRange(chunk_start, chunk_end)

    def _calculate_chunk_start(self, chunk_number: int) -> int:
        """Calculate the start of the chunk."""
        return self._chunk_size * chunk_number

    def _calculate_chunk_end(self, chunk_number: int, chunk_start: int) -> int:
        """Calculate the end of the chunk."""
        redundant_byte_offset: int = 1
        redundant_index_offset: int = 1

        if chunk_number < self._total_chunk_quantity - redundant_index_offset:
            return chunk_start + self._chunk_size - redundant_byte_offset

        return self._file_size - redundant_byte_offset


class FullFileDownloader:
    """Download regular sized file fully."""

    def __init__(
        self,
        session: ClientSession,
        url: Link,
        path_to_save: Path,
        semaphore: Semaphore,
    ):
        self._url = url
        self._path_to_save = path_to_save
        self._file_downloader = _FileDownloader(session, url, semaphore)

    async def download_file(self, timeout: ClientTimeout) -> None:
        file_name = self._file_downloader.extract_file_name_from_url()
        path_to_file = self._file_downloader.set_file_path(
            self._path_to_save, file_name
        )
        logger.info("...downloading %s", self._url)

        try:
            await self._file_downloader.execute_http_download(path_to_file, timeout)

        except asyncio.TimeoutError as e:
            logger.exception(
                "Unable to download %s, connection timed out",
                file_name,
            )
            raise DownloadError from e

        except Exception as e:
            logger.exception("Unable to download %s", file_name)
            raise DownloadError from e


class PartOfFileDownloader:
    """Download part of the file."""

    def __init__(
        self,
        session: ClientSession,
        url: Link,
        file_part_number: int,
        path_to_save: Path,
        semaphore: Semaphore,
        file_chunker: FileChunkCalculator,
    ):
        self._path_to_save = path_to_save
        self._file_downloader = _FileDownloader(session, url, semaphore)
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

        except Exception as e:
            logger.exception("Unable to set up arguments for download %s", file_name)
            raise DownloadError from e

        else:
            return part_file_path, headers

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


class _FileDownloader:
    def __init__(
        self,
        session: ClientSession,
        url: Link,
        semaphore: Semaphore,
    ):
        self._session = session
        self._url = url
        self._semaphore = semaphore
        self._chunk_size = CHUNK_SIZE

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

        except asyncio.TimeoutError as e:
            logger.exception("Unable to download %s, check your connection", file_name)
            raise DownloadError from e

        except Exception as e:
            logger.exception("Unable to download %s", file_name)
            raise DownloadError from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(NETWORK_ERRORS),
    )
    async def _try_execute_http_download(
        self,
        path_to_file: Path,
        timeout: ClientTimeout,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Download file and write its content to file."""
        async with (
            self._semaphore,
            self._session.get(self._url, headers=headers, timeout=timeout) as resp,
        ):
            await self._write_chunks_to_file(resp, path_to_file)

    async def _write_chunks_to_file(
        self, response: ClientResponse, path_to_file: Path
    ) -> None:
        """Write downloaded content to file piece by piece."""
        async with aiofiles.open(path_to_file, mode="wb") as output_file:
            async for chunk in response.content.iter_chunked(self._chunk_size):
                await output_file.write(chunk)
