from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Taxonomy:
    """NCBI Taxonomy info."""

    rank: str
    ncbi_id: int
    tax_name: str


@dataclass(frozen=True, slots=True)
class LineagePair:
    """Taxonomy lineage NCBI ID pairs."""

    main_taxid: int
    parent_taxid: int


@dataclass(frozen=True, slots=True)
class MergedPair:
    """NCBI IDs that were changed."""

    deprecated_id: int
    current_id: int
