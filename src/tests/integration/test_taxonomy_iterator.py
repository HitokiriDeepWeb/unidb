from pathlib import Path

import pytest

from domain.entities import Taxonomy
from infrastructure.process_data.ncbi import TaxonomyIterator


@pytest.fixture
def names_content() -> str:
    return (
        "2\t|\tBacteria\t|\tBacteria <bacteria>\t|\tscientific name\t|\n"
        "2\t|\tbacteria\t|\t\t|\tblast name\t|\n"
        "17\t|\tMethylophilus methylotrophus\t|\t\t|\tscientific name\t|\n"
        "139\t|\tBorreliella burgdorferi\t|\t\t|\tscientific name\t|\n"
        "204\t|\tCampylobacter showae\t|\t\t|\tscientific name\t|\n"
        "240\t|\tFlavobacterium sp. 141-8\t|\t\t|\tscientific name\t|"
    )


@pytest.fixture
def nodes_content() -> str:
    return (
        "2\t|\t131567\t|\tsuperkingdom\t|\t\t|\t0\t|\t0\t|\t11\t"
        "|\t0\t|\t0\t|\t0\t|\t0\t|\t0\t|\t\t|\t\t|\t\t|\t0\t|\t0\t|\t1\t|\n"
        "17\t|\t16\t|\tspecies\t|\tMM\t|\t0\t|\t1\t|\t11\t|\t1\t"
        "|\t0\t|\t1\t|\t1\t|\t0\t|\tcode compliant; specified\t|\t"
        "\t|\t\t|\t1\t|\t0\t|\t1\t|\n"
        "139\t|\t64895\t|\tspecies\t|\tBB\t|\t0\t|\t1\t|\t11\t|\t1\t"
        "|\t0\t|\t1\t|\t1\t|\t0\t|\tcode compliant; specified\t|\t\t"
        "|\t\t|1\t|\t0\t|\t1\t|\n"
        "204\t|\t194\t|\tspecies\t|\tCS\t|\t0\t|\t1\t|\t11\t|\t1\t"
        "|\t0\t|\t1\t|\t1\t|\t0\t|\tcode compliant; specified\t|\t"
        "\t|\t\t|\t1\t|\t0\t|\t1\t|\n"
        "240\t|\t196869\t|\tspecies\t|\tFS\t|\t0\t|\t1\t|\t11\t|\t"
        "1\t|\t0\t|\t1\t|\t1\t|\t0\t|\t\t|\t\t|\t\t|\t0\t|\t0\t|\t1\t|"
    )


@pytest.fixture
def path_to_names_dmp(tmp_path: Path, names_content: str) -> Path:
    path_to_file = tmp_path / "names.dmp"
    path_to_file.open("w").write(names_content)
    return path_to_file


@pytest.fixture
def path_to_nodes_dmp(tmp_path: Path, nodes_content: str) -> Path:
    path_to_file = tmp_path / "nodes.dmp"
    path_to_file.open("w").write(nodes_content)
    return path_to_file


def test_taxonomy_iterator_with_valid_content(
    path_to_nodes_dmp: Path, path_to_names_dmp: Path
):
    sut = TaxonomyIterator(
        path_to_ranks=path_to_nodes_dmp, path_to_names=path_to_names_dmp
    )
    expected_result = [
        Taxonomy(rank="superkingdom", ncbi_id=2, tax_name="Bacteria <bacteria>[2]"),
        Taxonomy(
            rank="species", ncbi_id=17, tax_name="Methylophilus methylotrophus[17]"
        ),
        Taxonomy(rank="species", ncbi_id=139, tax_name="Borreliella burgdorferi[139]"),
        Taxonomy(rank="species", ncbi_id=204, tax_name="Campylobacter showae[204]"),
        Taxonomy(rank="species", ncbi_id=240, tax_name="Flavobacterium sp. 141-8[240]"),
    ]

    result = list(sut)

    assert result == expected_result
