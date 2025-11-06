from io import StringIO

import pytest

from domain.entities import MergedPair
from infrastructure.process_data.exceptions import InvalidRecordError
from infrastructure.process_data.ncbi import (
    DelnodesParser,
    LineageParser,
    LineageTaxonomyIDs,
    MergedParser,
    NameData,
    NamesParser,
    RanksParser,
)

type NCBIParser = (
    DelnodesParser | LineageParser | MergedParser | NamesParser | RanksParser
)


def test_delnodes_parser_with_valid_content():
    source = StringIO("3121557\t|\n3121556\t|\n3121555\t|\n3121554\t|\n3121553\t|")
    expected_result = [
        3121557,
        3121556,
        3121555,
        3121554,
        3121553,
    ]
    sut = DelnodesParser()

    result = [sut.parse(line) for line in source]

    assert result == expected_result


def test_lineage_parser_with_valid_content():
    source = StringIO("2157\t|\t131567 \t|\n1935183\t|\t131567 2157 \t|")
    expected_result = [
        LineageTaxonomyIDs(2157, [131567]),
        LineageTaxonomyIDs(1935183, [131567, 2157]),
    ]
    sut = LineageParser()

    result = [sut.parse(line) for line in source]

    assert result == expected_result


def test_merged_parser_with_valid_content():
    source = StringIO(
        "12\t|\t74109\t|\n30\t|\t29\t|\n36\t|\t184914\t|\n37\t|\t42\t|\n46\t|\t39\t|"
    )
    expected_result = [
        MergedPair(deprecated_id=12, current_id=74109),
        MergedPair(deprecated_id=30, current_id=29),
        MergedPair(deprecated_id=36, current_id=184914),
        MergedPair(deprecated_id=37, current_id=42),
        MergedPair(deprecated_id=46, current_id=39),
    ]
    sut = MergedParser()

    result = [sut.parse(line) for line in source]

    assert result == expected_result


def test_names_parser_with_valid_content():
    source = StringIO(
        "2\t|\tBacteria\t|\tBacteria <bacteria>\t|\tscientific name\t|\n"
        "2\t|\tbacteria\t|\t\t|\tblast name\t|\n"
        "17\t|\tMethylophilus methylotrophus\t|\t\t|\tscientific name\t|\n"
        "139\t|\tBorreliella burgdorferi\t|\t\t|\tscientific name\t|\n"
        "204\t|\tCampylobacter showae\t|\t\t|\tscientific name\t|\n"
        "240\t|\tFlavobacterium sp. 141-8\t|\t\t|\tscientific name\t|"
    )
    expected_result = [
        NameData(ncbi_id=2, tax_name="Bacteria", specification="Bacteria <bacteria>"),
        None,
        NameData(ncbi_id=17, tax_name="Methylophilus methylotrophus", specification=""),
        NameData(ncbi_id=139, tax_name="Borreliella burgdorferi", specification=""),
        NameData(ncbi_id=204, tax_name="Campylobacter showae", specification=""),
        NameData(ncbi_id=240, tax_name="Flavobacterium sp. 141-8", specification=""),
    ]
    sut = NamesParser()

    result = [sut.parse(line) for line in source]

    assert result == expected_result


def test_ranks_parser_with_valid_content():
    source = StringIO(
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
    expected_result = [
        "superkingdom",
        "species",
        "species",
        "species",
        "species",
    ]
    sut = RanksParser()

    result = [sut.parse(line) for line in source]

    assert result == expected_result


@pytest.mark.parametrize(
    "parser",
    [
        LineageParser(),
        NamesParser(),
        RanksParser(),
        DelnodesParser(),
        MergedParser(),
    ],
)
def test_parsers_with_invalid_content(parser: NCBIParser):
    source = StringIO(
        "damaged_content|damaged_content|damaged_content||\tscientific name\t|"
    )

    with pytest.raises(InvalidRecordError):
        [parser.parse(line) for line in source]
