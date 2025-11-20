class FilePreparationError(Exception):
    """File preparation exception."""


class DownloadError(FilePreparationError):
    """Download exception"""
