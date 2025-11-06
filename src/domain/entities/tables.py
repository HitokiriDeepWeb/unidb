from enum import StrEnum


class Tables(StrEnum):
    """Tables that will be created in the UniProt database."""

    METADATA = "metadata"
    TAXONOMY = "taxonomy"
    LINEAGE = "lineage"
    UNIPROT = "uniprot_kb"
    MERGED = "merged_id"
