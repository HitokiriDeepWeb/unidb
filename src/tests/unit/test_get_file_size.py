import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from infrastructure.preparation.common_types import Link
from infrastructure.preparation.prepare_files.download import get_file_size


@pytest.mark.asyncio
async def test_get_file_size():
    file_size = 1000
    test_link = Link("http://example.com/test.txt")

    async with ClientSession(raise_for_status=True) as session:
        with aioresponses() as mock:
            mock.head(test_link, status=200, headers={"Content-Length": str(file_size)})
            result = await get_file_size(test_link, session)

    assert result == file_size
