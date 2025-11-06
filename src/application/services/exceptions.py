class ApplicationException(Exception):
    """Application level exceptions."""


class UniprotSetupError(ApplicationException):
    """Uniprot database Setup Error"""


class NoUpdateRequired(ApplicationException):
    """Raise when update is not required to finish the program"""
