from datetime import date
from pathlib import Path

import pytest
from aioresponses import aioresponses

from infrastructure.preparation.common_types import Link
from infrastructure.preparation.prepare_files.update_checker import UpdateChecker


@pytest.fixture
def test_path_to_modification_date(tmp_path: Path) -> Path:
    test_path = tmp_path / "last_modified_date.txt"

    test_path.open("w").write(str(date(2025, 1, 1)))
    return test_path


@pytest.mark.asyncio
async def test_update_checker(test_path_to_modification_date: Path):
    # Arrange.
    test_link = Link("http://example.com/test.txt")
    last_modified = str(date(2025, 1, 2))

    # Act.
    with aioresponses() as mock:
        mock.head(test_link, status=200, headers={"last-modified": last_modified})
        sut = UpdateChecker(
            url=test_link, path_to_modification_date=test_path_to_modification_date
        )

        if await sut.need_update():
            sut.save_database_update_time()

    result = (test_path_to_modification_date).open("r").read()

    # Assert.
    assert result == last_modified


@pytest.mark.asyncio
async def test_update_checker_was_retried_until_complete(
    test_path_to_modification_date: Path,
):
    # Arrange.
    test_link = Link("http://example.com/test.txt")
    last_modified = str(date(2025, 1, 2))

    # Act.
    with aioresponses() as mock:
        mock.head(test_link, status=500)
        mock.head(test_link, status=500)
        mock.head(test_link, status=200, headers={"last-modified": last_modified})
        sut = UpdateChecker(
            url=test_link, path_to_modification_date=test_path_to_modification_date
        )

        if await sut.need_update():
            sut.save_database_update_time()

    result = (test_path_to_modification_date).open("r").read()

    # Assert.
    assert result == last_modified
