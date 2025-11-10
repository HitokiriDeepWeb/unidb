import gzip
import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from core.exceptions import NeighbouringProcessError
from infrastructure.preparation.prepare_files import decompress_gz, extract_from_tar


@pytest.fixture
def test_tar(tmp_path: Path) -> Path:
    content = b"test tar"
    file_like_obj = BytesIO(content)
    tar_path = tmp_path / "test.tar"

    with tarfile.open(tar_path, "w") as archive:
        tar_info = tarfile.TarInfo(name="test.txt")
        tar_info.size = len(content)
        archive.addfile(tar_info, file_like_obj)

    return tar_path


@pytest.fixture
def test_gz(tmp_path: Path) -> Path:
    content = b"test gz"
    gz_path = tmp_path / "test.txt.gz"

    with gzip.open(gz_path, "wb") as file:
        file.write(content)

    return gz_path


def _mock_is_shutdown_event_set_func(mocker, flag: bool):
    return mocker.patch(
        "infrastructure.preparation.prepare_files.file_operations."
        "is_shutdown_event_set",
        return_value=flag,
    )


def _mock_set_shutdown_event_func(mocker):
    return mocker.patch(
        "infrastructure.preparation.prepare_files.file_operations.set_shutdown_event",
    )


def test_extract_from_tar(mocker, test_tar: Path, tmp_path: Path):
    _mock_is_shutdown_event_set_func(mocker, False)
    expected_result = b"test tar"

    extract_from_tar(path_to_file=test_tar, files_to_extract=("test.txt",))
    result = (tmp_path / "test.txt").open("rb").read()

    assert result == expected_result


def test_extract_from_tar_interrupted_when_shutdown_event_is_true(
    mocker, test_tar: Path
):
    _mock_is_shutdown_event_set_func(mocker, True)
    _mock_set_shutdown_event_func(mocker)

    with pytest.raises(NeighbouringProcessError):
        extract_from_tar(path_to_file=test_tar, files_to_extract=("test.txt",))


def test_decompress_gz(mocker, test_gz: Path, tmp_path: Path):
    _mock_is_shutdown_event_set_func(mocker, False)
    expected_result = b"test gz"

    decompress_gz(path_to_file=test_gz)
    result = (tmp_path / "test.txt").open("rb").read()

    assert result == expected_result


def test_decompress_gz_interrupted_when_shutdown_event_is_true(mocker, test_gz: Path):
    _mock_is_shutdown_event_set_func(mocker, True)
    _mock_set_shutdown_event_func(mocker)

    with pytest.raises(NeighbouringProcessError):
        decompress_gz(path_to_file=test_gz)
