from pathlib import Path

from domain.entities import BASE_DIR
from infrastructure.preparation.common_types import Link

UNIPROT_SP_LINK: Link = Link(
    "https://ftp.uniprot.org/pub/databases/uniprot/"
    "current_release/knowledgebase/complete/"
    "uniprot_sprot.fasta.gz"
)
UNIPROT_TR_LINK: Link = Link(
    "https://ftp.uniprot.org/pub/databases/uniprot/"
    "current_release/knowledgebase/complete/"
    "uniprot_trembl.fasta.gz"
)
UNIPROT_SP_ISOFORMS_LINK: Link = Link(
    "https://ftp.uniprot.org/pub/databases/uniprot/"
    "current_release/knowledgebase/complete/"
    "uniprot_sprot_varsplic.fasta.gz"
)
NCBI_LINK: Link = Link(
    "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz"
)

LAST_MODIFIED_DATE: Path = BASE_DIR / "last_modified.txt"
