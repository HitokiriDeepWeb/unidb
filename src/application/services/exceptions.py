class ApplicationError(Exception):
    """Application level exceptions."""


class UniprotSetupError(ApplicationError):
    """Uniprot database Setup Error"""


class NoUpdateRequired(ApplicationError):  # noqa: N818
    """Raise when update is not required to finish the program"""
