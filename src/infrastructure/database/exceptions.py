class DatabaseException(Exception):
    """Database level exception."""


class QueryExecutionError(DatabaseException):
    """Failed to execute database query exception"""


class ConnectionDatabaseError(DatabaseException):
    """Connection / pool creation exception"""


class ResetDatabaseError(DatabaseException):
    """Database reset exception."""
