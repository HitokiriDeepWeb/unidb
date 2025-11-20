class SystemPreparationError(Exception):
    """System preparation level exception."""


class NotEnoughSpaceError(SystemPreparationError):
    """Not enough disk space exception."""
