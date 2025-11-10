from pathlib import Path

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from core.config import SEMAPHORE, SMALL_FILE_TIMEOUT
from infrastructure.preparation.common_types import Link
from infrastructure.preparation.prepare_files.download import (
    FileChunkCalculator,
    FullFileDownloader,
    PartOfFileDownloader,
)
from infrastructure.preparation.prepare_files.download.downloader_components import (
    _FileDownloader,
)


@pytest.mark.asyncio
async def test_full_file_downloader(tmp_path: Path):
    # Arrange.
    test_body = b"Successful test"
    test_link = Link("http://example.com/test.txt")
    path_to_file = tmp_path / "test.txt"

    # Act.
    async with ClientSession(raise_for_status=True) as session:
        with aioresponses() as mock:
            mock.get(test_link, status=200, body=test_body)

            downloader = FullFileDownloader(
                session=session,
                url=test_link,
                path_to_save=tmp_path,
                semaphore=SEMAPHORE,
            )
            await downloader.download_file(timeout=SMALL_FILE_TIMEOUT)

    result = path_to_file.open("rb").read()

    # Assert.
    assert result == test_body


@pytest.mark.asyncio
async def test_part_file_downloader(tmp_path: Path):
    # Arrange.
    file_part_number = 1
    test_body = b"Successful test"
    file_size = len(test_body)
    chunk_calculator = FileChunkCalculator(
        file_size=file_size, total_chunk_quantity=file_part_number
    )
    test_link = Link("http://example.com/test.txt")

    # Act.
    async with ClientSession(raise_for_status=True) as session:
        with aioresponses() as mock:
            mock.get(test_link, status=206, body=test_body)

            downloader = PartOfFileDownloader(
                session=session,
                url=test_link,
                file_part_number=file_part_number,
                path_to_save=tmp_path,
                semaphore=SEMAPHORE,
                file_chunker=chunk_calculator,
            )
            await downloader.download_file(timeout=SMALL_FILE_TIMEOUT)

    result = (tmp_path / f"test.txt.{file_part_number}").open("rb").read()

    # Assert.
    assert result == test_body


@pytest.mark.asyncio
async def test_file_downloader_was_retried_until_complete(tmp_path: Path):
    # Arrange.
    test_body = b"Successful test"
    test_link = Link("http://example.com/test.txt")
    path_to_file = tmp_path / "test.txt"

    # Act.
    async with ClientSession(raise_for_status=True) as session:
        with aioresponses() as mock:
            mock.get(test_link, status=500)
            mock.get(test_link, status=500)
            mock.get(test_link, status=200, body=test_body)

            downloader = _FileDownloader(
                session=session, url=test_link, semaphore=SEMAPHORE
            )
            await downloader.execute_http_download(
                path_to_file=path_to_file, timeout=SMALL_FILE_TIMEOUT
            )

    result = path_to_file.open("rb").read()

    # Assert.
    assert result == test_body
