class SystemPreparationException(Exception):
    """System preparation level exception."""


class NotEnoughSpaceError(SystemPreparationException):
    """Not enough disk space exception."""
