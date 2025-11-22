from pathlib import Path

import pytest

from core.exceptions import NeighbouringProcessError
from infrastructure.preparation.prepare_files import concatenate_files
from infrastructure.preparation.prepare_files.exceptions import FilePreparationError


@pytest.fixture
def path_to_file(tmp_path: Path):
    file_name = "test.txt"
    base_file = tmp_path / file_name

    for index, word in enumerate(
        [
            "This ",
            "is ",
            "test ",
            "that ",
            "will ",
            "show ",
            "that ",
            "the ",
            "order ",
            "is ",
            "correct",
        ]
    ):
        with (tmp_path / f"{file_name}.{index}").open("w") as file:
            file.write(word)

    return base_file


def test_concatenate_files(mocker, path_to_file: Path):
    _mock_is_shutdown_event_set_func(mocker, False)
    expected_result = "This is test that will show that the order is correct"

    concatenate_files(path_to_file)
    result = path_to_file.open("r").read()

    assert result == expected_result


def test_concatenation_is_interrupted_when_shutdown_event_is_true(
    mocker, path_to_file: Path
):
    _mock_is_shutdown_event_set_func(mocker, True)

    with pytest.raises(NeighbouringProcessError):
        concatenate_files(path_to_file)


def test_concatenation_fails_and_shutdown_event_is_set(mocker, tmp_path: Path):
    _mock_is_shutdown_event_set_func(mocker, False)
    mocker_func = _mock_set_shutdown_event_func(mocker)

    with pytest.raises(FilePreparationError):
        concatenate_files(tmp_path)

    assert mocker_func.call_count == 1


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
