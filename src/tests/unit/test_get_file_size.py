import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from core.common_types import Link
from infrastructure.preparation import get_file_size


@pytest.mark.asyncio
async def test_get_file_size():
    file_size = 1000
    test_link = Link("http://example.com/test.txt")

    async with ClientSession(raise_for_status=True) as session:
        with aioresponses() as mock:
            mock.head(test_link, status=200, headers={"Content-Length": str(file_size)})
            result = await get_file_size(test_link, session)

    assert result == file_size


@pytest.mark.asyncio
async def test_get_file_size_when_content_length_header_is_not_available():
    test_link = Link("http://example.com/test.txt")

    async with ClientSession(raise_for_status=True) as session:
        with aioresponses() as mock:
            mock.head(test_link, status=200)

            with pytest.raises(KeyError):
                await get_file_size(test_link, session)
