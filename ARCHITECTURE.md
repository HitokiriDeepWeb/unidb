## Project Structure

```plaintext
unidb/
├── ARCHITECTURE.md                                           # Project architecture documentation.
├── CONTRIBUTING.md                                           # Contribution guidelines.
├── LICENSE                                                   # Project license.
├── Makefile                                                  # Make scripts and commands.
├── pyproject.toml                                            # Python project configuration and dependencies.
├── README.md                                                 # Main project documentation
├── src
│   ├── application                                           # Application layer.
│   │   ├── __init__.py
│   │   ├── interfaces.py                                     # Application interfaces.
│   │   ├── models.py                                         # Application data models.
│   │   └── services                                          # Application services.
│   │       ├── copy_files.py                                 # File-to-database data copying service.
│   │       ├── exceptions.py                                 # Application exceptions.
│   │       ├── __init__.py
│   │       ├── setup_uniprot_database.py                     # Main orchestration service that will setup UniProt database.
│   │       └── uniprot_operator.py                           # UniProt operator.
│   ├── core                                                  # Core system components.
│   │   ├── config.py                                         # Project config.
│   │   ├── common_types.py                                   # Common types that may be used elsewhere.
│   │   ├── exceptions.py                                     # Common exceptions that may be used elsewhere.
│   │   ├── __init__.py
│   │   ├── interfaces.py                                     # Common interfaces that may be used elsewhere.
│   │   ├── logging_config.py                                 # Logging configuration.
│   │   ├── models.py                                         # Models that may be used elsewhere.
│   │   └── utils                                             # Common utilities that may be used elsewhere.
│   │       ├── __init__.py
│   │       ├── process_awaitables.py                         # Process async tasks and futures.
│   │       ├── process_globals.py                            # Global variables and functions to handle shutdown event in multiprocessing environment.
│   │       └── time_measure.py                               # Time measurement for development.
│   ├── domain                                                # Domain layer (business logic). May be used elsewhere.
│   │   ├── entities                                          # Domain entities.
│   │   │   ├── constants.py                                  # Domain constants.
│   │   │   ├── __init__.py
│   │   │   ├── sequence.py                                   # UniProt Sequence entities.
│   │   │   ├── tables.py                                     # Table entities.
│   │   │   └── taxonomy.py                                   # NCBI Taxonomy entities.
│   │   ├── exceptions.py                                     # Domain exceptions.
│   │   ├── __init__.py
│   │   ├── interfaces.py                                     # Domain interfaces.
│   │   ├── models.py                                         # Domain models.
│   │   └── services
│   │       ├── batch_copier.py                               # Batch copying service. Copies data to the UniProt database.
│   │       └── queue_manager                                 # Asynchronous queue manager.
│   │           ├── config.py                                 # Config for queue manager
│   │           ├── __init__.py
│   │           └── queue_manager.py                          # Asynchronous queue manager implementation.
│   ├── infrastructure                                        # Infrastructure layer.
│   │   ├── database                                          # Database operations and data.
│   │   │   ├── common_types.py                               # Database module type definitions.
│   │   │   ├── exceptions.py                                 # Database exceptions.
│   │   │   ├── __init__.py
│   │   │   └── postgresql                                    # PostgreSQL operations and data.
│   │   │       ├── adapter.py                                # PostgreSQL adapter.
│   │   │       ├── config.py                                 # Configuration data structures.
│   │   │       ├── uniprot_lifecycle.py                      # PostgreSQL UniProt operations that constitute UniProt database lifecycle.
│   │   │       ├── __init__.py
│   │   │       ├── queries.py                                # SQL queries.
│   │   │       └── setup_config.py                           # Database setup configuration.
│   │   ├── __init__.py
│   │   ├── preparation                                       # System and file preparation.
│   │   │   ├── common_types.py                               # Preparation module type definitions.
│   │   │   ├── get_file_size.py                              # File size retrieval.
│   │   │   ├── __init__.py
│   │   │   ├── prepare_files                                 # File preparation.
│   │   │   │   ├── download                                  # File downloading.
│   │   │   │   │   ├── downloader_components.py              # Downloader components.
│   │   │   │   │   ├── downloader.py                         # Download orchestration.
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── exceptions.py                             # Preparation exceptions.
│   │   │   │   ├── file_operations.py                        # Operations that will prepare files (extract, decompress, concatenate, etc.)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── preparer.py                               # File preparation orchestrator.
│   │   │   │   └── update_checker.py                         # Update checker.
│   │   │   └── prepare_system                                # System preparation.
│   │   │       ├── config.py                                 # Configuration for system preparer.
│   │   │       ├── exceptions.py                             # System preparation exceptions.
│   │   │       ├── __init__.py
│   │   │       ├── models.py                                 # Preparation models.
│   │   │       └── preparer.py                               # System preparation orchestrator.
│   │   ├── process_data                                      # Data processing.
│   │   │   ├── exceptions.py                                 # Processing exceptions.
│   │   │   ├── __init__.py
│   │   │   ├── iterator_table_mapping.py                     # Maps iterators to tables.
│   │   │   ├── ncbi                                          # NCBI data processing.
│   │   │   │   ├── __init__.py
│   │   │   │   ├── iterators                                 # NCBI iterators.
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── ncbi_iterator.py                      # General NCBI files iterator.
│   │   │   │   │   └── taxonomy_iterator.py                  # Iterate over files that will compose data for Taxonomy table.
│   │   │   │   ├── models.py                                 # NCBI models.
│   │   │   │   ├── parsers.py                                # NCBI parsers.
│   │   │   │   ├── presenters.py                             # NCBI data presenters.
│   │   │   │   └── utils.py                                  # Utils to work with NCBI functions.
│   │   │   └── uniprot                                       # Working with UniProt data.
│   │   │       ├── fasta                                     # FASTA format.
│   │   │       │   ├── chunk_range_iterator.py               # FASTA file chunk iterator.
│   │   │       │   ├── __init__.py
│   │   │       │   ├── iterator.py                           # FASTA file iterator.
│   │   │       │   └── parser.py                             # FASTA file parser.
│   │   │       └── __init__.py
│   │   └── ui                                                # User interface.
│   │       ├── cli.py                                        # CLI interface.
│   │       └── __init__.py
│   ├── __init__.py
│   ├── main.py                                               # Project entrypoint.
│   └── tests                                                 # Project tests.
│       ├── integration                                       # Integration tests.
│       └── unit                                              # Unit tests.
└── uv.lock                                                   # Dependency version lock file (uv).
```
