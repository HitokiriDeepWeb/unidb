from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConnectionConfig:
    """

    Configuration dictionary for database connection parameters.

    database: Name of the database to connect to
    user: Username for database authentication
    port: TCP port number for database connection
    host: Database server hostname or IP address
    password: Password for database authentication
    """

    database: str
    user: str
    port: int
    host: str
    password: str


@dataclass(frozen=True, slots=True)
class ConnectionPoolConfig(ConnectionConfig):
    """
    Configuration dictionary for database connection pool parameters.

    database: Name of the database to connect to
    user: Username for database authentication
    port: TCP port number for database connection
    host: Database server hostname or IP address
    password: Password for database authentication
    min_size: Minimum number of database connections in the connection pool
    max_size: Maximum number of database connections in the connection pool
    """

    min_size: int
    max_size: int
