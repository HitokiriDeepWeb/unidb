from pathlib import Path

import pytest

from domain.entities import LineagePair, MergedPair, Taxonomy
from infrastructure.process_data.ncbi import (
    NCBIIterator,
    PresenterType,
)


@pytest.fixture
def merged_content() -> str:
    return "12\t|\t74109\t|\n30\t|\t29\t|\n36\t|\t184914\t|\n37\t|\t42\t|\n46\t|\t39\t|"


@pytest.fixture
def delnodes_content() -> str:
    return "3121557\t|\n3121556\t|\n3121555\t|\n3121554\t|\n3121553\t|"


@pytest.fixture
def lineage_content() -> str:
    return "2157\t|\t131567 \t|\n1935183\t|\t131567 2157 \t|"


@pytest.fixture
def test_merged_dmp(tmp_path: Path, merged_content: str) -> Path:
    path_to_file = tmp_path / "test.dmp"
    path_to_file.open("w").write(merged_content)
    return path_to_file


@pytest.fixture
def test_delnodes_dmp(tmp_path: Path, delnodes_content: str) -> Path:
    path_to_file = tmp_path / "test.dmp"
    path_to_file.open("w").write(delnodes_content)
    return path_to_file


@pytest.fixture
def test_lineage_dmp(tmp_path: Path, lineage_content: str) -> Path:
    path_to_file = tmp_path / "test.dmp"
    path_to_file.open("w").write(lineage_content)
    return path_to_file


def test_ncbi_iterator_with_delnodes_file(test_delnodes_dmp: Path):
    sut = NCBIIterator(test_delnodes_dmp, PresenterType.DELNODES)
    expected_result = [
        Taxonomy(rank="no rank", ncbi_id=3121557, tax_name="deleted[3121557]"),
        Taxonomy(rank="no rank", ncbi_id=3121556, tax_name="deleted[3121556]"),
        Taxonomy(rank="no rank", ncbi_id=3121555, tax_name="deleted[3121555]"),
        Taxonomy(rank="no rank", ncbi_id=3121554, tax_name="deleted[3121554]"),
        Taxonomy(rank="no rank", ncbi_id=3121553, tax_name="deleted[3121553]"),
    ]

    result = list(sut)

    assert result == expected_result


def test_ncbi_iterator_with_lineage_file(test_lineage_dmp: Path):
    sut = NCBIIterator(test_lineage_dmp, PresenterType.LINEAGE)
    expected_result = [
        LineagePair(main_taxid=2157, parent_taxid=2157),
        LineagePair(main_taxid=2157, parent_taxid=131567),
        LineagePair(main_taxid=1935183, parent_taxid=1935183),
        LineagePair(main_taxid=1935183, parent_taxid=131567),
        LineagePair(main_taxid=1935183, parent_taxid=2157),
    ]

    result = list(sut)

    assert result == expected_result


def test_ncbi_iterator_with_merged_file(test_merged_dmp: Path):
    sut = NCBIIterator(test_merged_dmp, PresenterType.MERGED)
    expected_result = [
        MergedPair(deprecated_id=12, current_id=74109),
        MergedPair(deprecated_id=30, current_id=29),
        MergedPair(deprecated_id=36, current_id=184914),
        MergedPair(deprecated_id=37, current_id=42),
        MergedPair(deprecated_id=46, current_id=39),
    ]

    result = list(sut)

    assert result == expected_result
