from enum import StrEnum


class NCBIFiles(StrEnum):
    RANKS = "nodes.dmp"
    NAMES = "names.dmp"
    LINEAGE = "taxidlineage.dmp"
    MERGED = "merged.dmp"
    DELNODES = "delnodes.dmp"


class UniprotFiles(StrEnum):
    SWISS_PROT = "uniprot_sprot.fasta"
    SP_ISOFORMS = "uniprot_sprot_varsplic.fasta"
    TREMBL = "uniprot_trembl.fasta"
