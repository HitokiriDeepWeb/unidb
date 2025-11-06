from collections.abc import Iterator
from typing import TextIO

from domain.entities import LineagePair, MergedPair, Taxonomy
from infrastructure.process_data.ncbi.models import LineageTaxonomyIDs
from infrastructure.process_data.ncbi.parsers import (
    DelnodesParser,
    LineageParser,
    MergedParser,
)


class DelnodesPresenter:
    """
    Generate a pair in the format: 'no rank|deleted_id|deleted[deleted_id]'.

    Example input line: '3418941\t|'.
    Output: dataclass_name('no rank', 3418941, 'deleted').
    """

    def __init__(self):
        self._parser = DelnodesParser()

    def present(self, source: TextIO) -> Iterator[Taxonomy]:
        for line in source:
            deleted_ncbi_id: int = self._parser.parse(line)
            yield Taxonomy("no rank", deleted_ncbi_id, f"deleted[{deleted_ncbi_id}]")


class LineagePresenter:
    """
    Generate  pairs with taxon-parent relationships
    in the format 'taxon_id|parent_taxid'.

    Example line: '12345\t|\t1|2|3|4\t|\n' (taxidlineage.dmp).
    Output lines:
      dataclass_name(12345 12345)
      dataclass_name(12345 1)
      dataclass_name(12345 2)
      dataclass_name(12345 3)
      dataclass_name(12345 4)
    """

    def __init__(self):
        self._parser = LineageParser()

    def present(self, source: TextIO) -> Iterator[LineagePair]:
        for line in source:
            taxids = self._parser.parse(line)
            yield from self._cartesian_pairs_gen(taxids)

    def _cartesian_pairs_gen(self, taxids: LineageTaxonomyIDs) -> Iterator[LineagePair]:
        """Generate 'main - main', 'main - parent' cartesian pairs."""
        yield LineagePair(taxids.main_taxid, taxids.main_taxid)

        for parent in taxids.parent_taxids:
            yield LineagePair(taxids.main_taxid, parent)


class MergedPresenter:
    """Generate dataclass_name(deprecated_id, current_id)."""

    def __init__(self):
        self._parser = MergedParser()

    def present(self, source: TextIO) -> Iterator[MergedPair]:
        for line in source:
            yield self._parser.parse(line)


NCBI_PRESENTERS: dict[str, DelnodesPresenter | LineagePresenter | MergedPresenter] = (
    dict(
        delnodes_presenter=DelnodesPresenter(),
        lineage_presenter=LineagePresenter(),
        merged_presenter=MergedPresenter(),
    )
)
