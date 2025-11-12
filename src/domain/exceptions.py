class DomainError(Exception):
    """Domain level exceptions."""


class CopyToUniprotDBError(DomainError):
    """Copy to uniprot database exception."""
