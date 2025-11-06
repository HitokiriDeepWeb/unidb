class DataProcessingException(Exception):
    """Data processing level exception."""


class InvalidRecordError(DataProcessingException):
    """Invalid record structure exception."""


class IteratorError(DataProcessingException):
    """File iteration exception."""
