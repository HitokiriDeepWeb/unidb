class DataProcessingError(Exception):
    """Data processing level exception."""


class InvalidRecordError(DataProcessingError):
    """Invalid record structure exception."""


class IteratorError(DataProcessingError):
    """File iteration exception."""
