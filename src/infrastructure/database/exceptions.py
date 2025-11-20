class DatabaseError(Exception):
    """Database level exception."""


class QueryExecutionError(DatabaseError):
    """Failed to execute database query exception"""


class ConnectionDatabaseError(DatabaseError):
    """Connection / pool creation exception"""


class ResetDatabaseError(DatabaseError):
    """Database reset exception."""
