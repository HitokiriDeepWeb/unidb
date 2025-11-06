from dataclasses import dataclass
from enum import StrEnum


class PresenterType(StrEnum):
    DELNODES = "delnodes_presenter"
    LINEAGE = "lineage_presenter"
    MERGED = "merged_presenter"


@dataclass(frozen=True, slots=True)
class NameData:
    """Info from names.dmp file."""

    ncbi_id: int
    tax_name: str
    specification: str


@dataclass(frozen=True, slots=True)
class LineageTaxonomyIDs:
    """Lineage taxon IDs including all parent IDs."""

    main_taxid: int
    parent_taxids: list[int]
