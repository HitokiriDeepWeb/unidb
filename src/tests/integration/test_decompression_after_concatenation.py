import gzip
from pathlib import Path

import pytest

from infrastructure.preparation.prepare_files.file_operations import (
    concatenate_files,
    decompress_gz,
)

CONTENT = (
    b">tr|A0A023T699|A0A023T699_EMCV Genome polyprotein "
    b"OS=Encephalomyocarditis virus OX=12104 PE=3 SV=1\n"
    b"MATTMEQETCAHPLTFEECPKCSALQYRNGF\n"
    b"YLLKYDEEWYPEELLIDGEDDVFDPELDMES\n"
    b"VEYRWRSLFW\n"
    b">sp|A0A076FVY1|A0A076FVY1_BATSU Tyrosine-protein kinase receptor (Fragment) "
    b"OS=Bathyergus suillus OX=10172 GN=IGF1R PE=2 SV=1\n"
    b"ASELENFMGLIEVVTGYVKIRHSHALVSLSF\n"
    b"LKNLRQILGEEQLEGNYSFYVLDNQNLQQPG\n"
    b"VLVLRASFDERQPYAHMNGGRTNERA\n"
    b"LPLPQSSTC\n"
)


@pytest.fixture
def test_gz(tmp_path: Path) -> Path:
    gz_path = tmp_path / "test.txt.gz"

    with gzip.open(gz_path, "wb") as file:
        file.write(CONTENT)

    return gz_path


def test_decompression_is_working_properly_after_concatenation(mocker, test_gz: Path):
    _mock_is_shutdown_event_set_func(mocker, False)
    gz_parts = 18
    gz_content = Path(f"{test_gz}").open("rb").read()
    gz_size = test_gz.stat().st_size
    chunk_size = gz_size // gz_parts

    for part in range(gz_parts):
        start = part * chunk_size
        end = (part + 1) * chunk_size if part < gz_parts - 1 else len(gz_content)
        part_content = gz_content[start:end]

        Path(f"{test_gz}.{part}").open("wb").write(part_content)

    test_gz.unlink()

    # Act.
    concatenate_files(test_gz)
    decompress_gz(test_gz)
    result_content = Path(f"{test_gz.parent}/test.txt").open("rb").read()

    # Assert.
    assert result_content == CONTENT


def _mock_is_shutdown_event_set_func(mocker, flag: bool):
    return mocker.patch(
        "infrastructure.preparation.prepare_files.file_operations."
        "is_shutdown_event_set",
        return_value=flag,
    )
