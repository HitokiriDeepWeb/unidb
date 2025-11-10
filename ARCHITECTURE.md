## Project Structure

```plaintext
unidb/
├── ARCHITECTURE.md
├── LICENSE
├── Makefile
├── pyproject.toml
├── README.md
├── src
│   ├── application
│   │   ├── __init__.py
│   │   ├── interfaces.py
│   │   ├── models.py
│   │   └── services
│   │       ├── copy_files.py
│   │       ├── exceptions.py
│   │       ├── __init__.py
│   │       ├── setup_uniprot_database.py
│   │       └── uniprot_operator.py
│   ├── core
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── __init__.py
│   │   ├── interfaces.py
│   │   ├── logging_config.py
│   │   ├── models.py
│   │   └── utils
│   │       ├── __init__.py
│   │       ├── process_awaitables.py
│   │       ├── process_globals.py
│   │       └── time_measure.py
│   ├── domain
│   │   ├── entities
│   │   │   ├── constants.py
│   │   │   ├── __init__.py
│   │   │   ├── sequence.py
│   │   │   ├── tables.py
│   │   │   └── taxonomy.py
│   │   ├── exceptions.py
│   │   ├── __init__.py
│   │   ├── interfaces.py
│   │   ├── models.py
│   │   └── services
│   │       ├── batch_copier.py
│   │       └── queue_manager
│   │           ├── config.py
│   │           ├── __init__.py
│   │           └── queue_manager.py
│   ├── infrastructure
│   │   ├── database
│   │   │   ├── common_types.py
│   │   │   ├── exceptions.py
│   │   │   ├── __init__.py
│   │   │   └── postgresql
│   │   │       ├── adapter.py
│   │   │       ├── config.py
│   │   │       ├── uniprot_lifecycle.py
│   │   │       ├── __init__.py
│   │   │       ├── queries.py
│   │   │       └── setup_config.py
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── preparation
│   │   │   ├── common_types.py
│   │   │   ├── __init__.py
│   │   │   ├── prepare_files
│   │   │   │   ├── download
│   │   │   │   │   ├── download_components.py
│   │   │   │   │   ├── downloader.py
│   │   │   │   │   ├── file_chunker.py
│   │   │   │   │   ├── get_file_size.py
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── file_operations.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── preparer.py
│   │   │   │   └── update_checker.py
│   │   │   └── prepare_system
│   │   │       ├── config.py
│   │   │       ├── exceptions.py
│   │   │       ├── __init__.py
│   │   │       ├── models.py
│   │   │       └── preparer.py
│   │   ├── process_data
│   │   │   ├── exceptions.py
│   │   │   ├── __init__.py
│   │   │   ├── iterator_table_mapping.py
│   │   │   ├── ncbi
│   │   │   │   ├── __init__.py
│   │   │   │   ├── iterators
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── ncbi_iterator.py
│   │   │   │   │   └── taxonomy_iterator.py
│   │   │   │   ├── models.py
│   │   │   │   ├── parsers.py
│   │   │   │   ├── presenters.py
│   │   │   │   └── utils.py
│   │   │   └── uniprot
│   │   │       ├── fasta
│   │   │       │   ├── chunk_range_iterator.py
│   │   │       │   ├── __init__.py
│   │   │       │   ├── iterator.py
│   │   │       │   └── parser.py
│   │   │       └── __init__.py
│   │   └── ui
│   │       ├── cli.py
│   │       └── __init__.py
│   ├── __init__.py
│   ├── main.py
│   └── tests
│       ├── integration
│       └── unit
└── uv.lock
```
