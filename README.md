# UniProt Database Creator `unidb`

## Table of Contents

- [Purpose](#purpose)
- [Licenses](#licenses)
- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
  - [Syntax](#syntax)
  - [Required Parameters](#required-parameters)
  - [Optional Parameters](#optional-parameters)
  - [Basic Example](#basic-example)
  - [Advanced Example with Optimization](#advanced-example-with-optimization)
  - [Using Pre-downloaded And Extracted Decompressed Files](#using-pre-downloaded-and-extracted-decompressed-files)
  - [Notes](#notes)
- [System Requirements and Prerequisites](#system-requirements-and-prerequisites)
- [Main Terms (briefly)](#main-terms-briefly)
- [Database](#database)
  - [General Information](#general-information)
  - [Database Structure](#database-structure)
  - [Database Sources](#database-sources)
  - [Taxonomy](#taxonomy)
  - [Isoforms](#isoforms)
- [Technical Details](#technical-details)
  - [Supported Databases](#supported-databases)
  - [Performance](#performance)
- [Troubleshooting](#troubleshooting)
  - [Common Issues](#common-issues)
- [Program Structure](#program-structure)

## Purpose

This application is designed to create and configure a UniProt database with parallel processing capabilities and flexible logging configuration.

As an alternative to setting up your own UniProt database, you may use existing web interfaces:

- **UniProt peptide search**: [https://www.uniprot.org/peptide-search](https://www.uniprot.org/peptide-search) - searches for sequences ≥7 amino acids.
- **pepstring**: [http://pepstring.eimb.ru/](http://pepstring.eimb.ru/) - searches for sequences ≥3 amino acids.

## Licenses

This program uses and downloads data from UniProt and NCBI FTP sites.

All data from UniProt is distributed under license:
**Creative Commons Attribution 4.0 International (CC BY 4.0)**.

**License Terms**:

- You may freely copy, distribute, and adapt the data
- You must provide appropriate attribution

**Attribution**:

- Data Source: UniProt Knowledgebase (via FTP)
- License: CC BY 4.0
- License Link: https://creativecommons.org/licenses/by/4.0/
- Source Link: https://www.uniprot.org/help/license

All data from NCBI FTP is public, non-sensitive, unrestricted scientific data sharing among scientific communities.

**Terms of Use**:

- You may freely copy, distribute, and adapt the data for scientific use.
- You must provide appropriate attribution to NCBI and the original data sources.
- You should not present NCBI data as your own.

**Attribution**:

- Data Source: National Center for Biotechnology Information (NCBI)
- Terms of Use: https://www.ncbi.nlm.nih.gov/home/about/policies/
- Source Link: https://ftp.ncbi.nih.gov/pub/README.ftp
- Data accessed via: https://ftp.ncbi.nlm.nih.gov/

This program is distributed under the MIT license.

- License: MIT
- License Link: https://mit-license.org/

_This software creates a derivative database based on the original UniProt and NCBI data. The derivative database is distributed under the same terms of the CC BY 4.0 license. You should not present NCBI data as your own_.

## Introduction

This util will create UniProt database using official data from [UniProt FTP site](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/) and [NCBI FTP site](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/).

## Installation

Download the `unidb.pex` file.

## Usage

### Syntax

```bash
./unidb.pex [OPTIONS]
```

Or

```bash
python unidb.pex [OPTIONS]
```

### Required Parameters

`--dbname`, `-d`

- Description: PostgreSQL database name
- Type: string
- Example: `--dbname uniprot_db` or `-d uniprot_db`

`--dbuser`, `-U`

- Description: Database username
- Type: string
- Example: `--dbuser postgres` or `-U postgres`

### Optional Parameters

`--password`, `-p`

- Description: Database password
- Type: string
- Example: `--password mypassword`

`--port`, `-P`

- Description: PostgreSQL connection port
- Type: positive integer
- Default: 5432
- Example: `--port 5433`

`--host`, `-u`

- Description: Database host
- Type: string
- Default: localhost
- Example: `--host 192.168.1.100`

`--processes`, `-j`

- Description: Number of processes for work distribution
- Type: positive integer
- Default: 1
- Example: `--processes 4` (to use 4 CPU cores)

`--path-to-source-files`, `-k`

- Description: Path to pre-downloaded unpacked source files
- Type: directory path
- Example: `--path-to-source-files /path/to/uniprot/files`

`--path-to-source-archives`, `-z`

- Description: Path to pre-downloaded archives
- Type: directory path
- Example: `--path-to-source-archives /path/to/uniprot/archives`

`-y`

- Description: Automatically accept all conditions and setup
- Type: flag (no value required)
- Example: `-y`

`--trgm`, `-i`

- Description: Build trigram index on sequence column in uniprot_kb table
- Type: flag
- Example: `--trgm` (improves sequence search performance)

`--verbose`, `-v`

- Description: Enable detailed logging
- Type: flag
- Example: `--verbose`

`--logtype`, `-t`

- Description: Log output destination
- Type: console | file
- Default: console
- Example: `--logtype file`

`--loglevel`, `-l`

- Description: Log detail level
- Type: string (debug, info, warning, error, critical)
- Default: info
- Example: `--loglevel debug`

`--logpath`, `-L`

- Description: Directory path for log files
- Type: directory path
- Default: uniprotdb/logs
- Example: `--logpath /var/log/uniprot`

### Basic Example

```bash
./unidb.pex -d uniprot_database -U postgres -p mypassword
```

### Advanced Example with Optimization

```bash
./unidb.pex \
  -d uniprot_prod \
  -U dbadmin \
  -p securepass \
  -j 8 \
  -i \
  -y \
  -v \
  -t file \
  -L /var/log/uniprot
```

### Using Pre-downloaded And Extracted Decompressed Files

```bash
./unidb.pex \
  -d uniprot_test \
  -U tester \
  -k /home/user/uniprot_files \
  -j 4 \
  -i
```

### Notes

It is recommended to use -j with number of CPU cores.
The -i (trgm) flag improves sequence search performance but increases database creation time and almost doubles the database size.
When using -y, all confirmations are accepted automatically.

Required source files in case you use `--path-to-source-files`, `-k` option:

- **names.dmp**
- **nodes.dmp**
- **delnodes.dmp**
- **merged.dmp**
- **taxidlineage.dmp**
- **uniprot_sprot.fasta**
- **uniprot_sprot_varsplic.fasta**
- **uniprot_treml.fasta**

Required archives in case you use `--path-to-source-archives`, `-z` option:

- [new_taxdump.tar.gz](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz)
- [uniprot_sprot.fasta.gz](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_sprot.fasta.gz)
- [uniprot_sprot_varsplic.fasta.gz](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_sprot_varsplic.fasta.gz)
- [uniprot_trembl.fasta.gz](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/uniprot_trembl.fasta.gz)

## System Requirements And Prerequisites

- **Python** 3.12+
- **PostgreSQL** 9+
- **\*nix system** (Linux, macOS)
- `cat` utility
- **Internet connection** (unless using pre-downloaded files)

To create database without trigram index and download all the files you will need approximately 205 GB free space.
The database itself after setup will weigh approximately 108 GB.

To create database with trgm index and download all the files you will need approximately 215 GB free space.

## Main Terms (briefly)

- _UniProtKB_ - is a collection of peptide sequences which in place consists of two main partitions - TrEMBL and Swiss-Prot.
- _TrEMBL_ - peptide sequences that were computationally analyzed but not reviewed by humans.
- _Swiss-Prot_ - peptide sequences that were manually reviewed by humans.
- _Accession_ - protein sequence unique identifier (ID) from UniProtKB.
- _Entry name_ - protein sequence former ID with biological info from UniProtKB.

- _Taxonomy_ - is the study that name, group, classify organisms and put them into hierarchy. This hierarchy is called _taxonomic lineage_. (Do not mix organism names (from peptide table) and taxons (from taxonomy table). Taxons include all the organism names but not vice versa.)
- _Lineage_ - taxonomic lineage is a hierarchy which illustrates relationships between organisms. This hierarchy is divided by rank (domain, kingdom, phylum, class, order, family, genus, species, etc.). What is important - different organisms may share the same taxons and that is where we can trace their relations. (For example humans and rats have some common taxons. One of them is Vertebrata(vertebrates)).
- _NCBI ID_ - ID of taxons from the NCBI Taxonomy database.

## Database

### General Information

The database contains data from [UniProtKB](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/) and [NCBI Taxonomy](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/) knowledgebases.

### Database Structure

The database consists of four tables:

**uniprot_kb** - protein sequence database from UniProtKB (Swiss-Prot and Isoforms + TrEMBL).

- **source**: source database - 'sp' (Swiss-Prot), 'tr' (TrEMBL), 'sp_iso' (reviewed isoforms).
- **is_reviewed**: whether the sequence was manually reviewed/curated.
- **accession**: unique protein accession ID.
- **entry_name**: protein entry name containing biological information.
- **peptide_name**: full name/description of the protein.
- **ncbi_organism_id**: NCBI taxon ID of the source organism.
- **organism_name**: scientific name of the source organism.
- **sequence**: protein amino acid sequence (single letter codes).

**taxonomy** - NCBI Taxonomy database information:

- **rank**: taxonomic rank (e.g., species, genus, family).
- **ncbi_taxon_id**: unique NCBI taxonomy identifier.
- **tax_name**: scientific name of the taxon.

**lineage** - taxonomic lineage relationships:

- **ncbi_taxon_id**: organism taxon ID. Organism is the last taxon in the lineage.
- **ncbi_lineage_id**: ancestor taxon ID in the lineage.
  This table stores the complete taxonomic hierarchy for each organism, linking organisms to all their ancestral taxa.

**metadata** - contains licensing and attribution information for the database sources:

- **data_source**: Name of the data source (e.g., "UniProt Knowledgebase FTP", "NCBI FTP").
- **data_license**: License type for the data (e.g., "CC BY 4.0", "Public unrestricted scientific data").
- **license_url**: URL to the full license text.
- **attribution_required**: Whether attribution is required ("Yes"/"No").
  This table stores the legal and attribution requirements for using the database content.

### Database Sources

The database is made on the basis of two knowledgebases - [UniProtKB](https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/) and [NCBI Taxonomy](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/)

### Taxonomy

The taxonomy is implemented identical to the NCBI taxonomy. Note that NCBI IDs and organism names may not coincide with data from UniProt knowledgebase.
The reason is that UniProt updates its taxonomy once every 8 weeks. However, current database uses NCBI Taxonomy which receives new updates daily so it might happen that version the database uses for update differs from version UniProt did. If you see '_deleted_' in taxonomy list - it means there is <ins>no lineage for this taxon in the database</ins>. For more information about this _taxon_ you should move to [UniProt official site](https://www.uniprot.org/) or [NCBI Taxonomy Browser](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi).

### Isoforms

Only additional manually curated isoform sequences that are described in UniProtKB/Swiss-Prot from _uniprot_sprot_varsplic.fasta.gz_ are available.

## Technical Details

### Supported Databases

Currently only **PostgreSQL** database is supported.

### Performance

Using `-j` with CPU cores significantly improves performance. Trigram index improves search speed but increases build time tremendously and doubles the storage size.

**Test environment**

- **OS**: Ubuntu 24.04
- **Database**: PostgreSQL 16
- **Python**: 3.13
- **CPU**: 12 cores
- **RAM**: 8 GB
- **Storage**: SSD 235 GB NVMe
- **Internet**: 250 Mb/s

**Standard Setup**:

```bash
./unidb.pex \
  --dbname database_name \
  --dbuser database_user \
  --password 'password' \
  -j 12 \
  --logtype file \
  --loglevel DEBUG \
  --verbose \
  -y
```

**Estimated time**: ~1 hour.

**With Trigram Index**:

```bash
./unidb.pex \
  --dbname database_name \
  --dbuser database_user \
  --password 'password' \
  -j 12 \
  --logtype file \
  --loglevel DEBUG \
  --verbose \
  --trgm \
  -y
```

**Estimated time**: ~6 hours 30 minutes.

## Troubleshooting

### Common Issues

#### Connection Issues:

Ensure PostgreSQL is running and accessible.
Verify connection parameters (host, port, credentials).
Check user permissions for database creation.

#### Disk Space:

Monitor free space during database creation.
Use `--path-to-source-files` or `--path-to-source-archives` for external storage.

#### Memory Issues:

Reduce parallel processes with `-j` parameter.
Increase system swap space if needed.

#### Build Failures:

Check PostgreSQL version.
Verify all prerequisites are met.

## Program Structure

```bash
unidb
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
│   │   │       ├── database_lifecycle.py
│   │   │       ├── get_available_connections_amount.py
│   │   │       ├── __init__.py
│   │   │       ├── queries.py
│   │   │       └── setup_config.py
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── preparation
│   │   │   ├── common_types.py
│   │   │   ├── constants.py
│   │   │   ├── __init__.py
│   │   │   ├── prepare_files
│   │   │   │   ├── download
│   │   │   │   │   ├── config.py
│   │   │   │   │   ├── downloader.py
│   │   │   │   │   ├── download_files.py
│   │   │   │   │   ├── file_chunker.py
│   │   │   │   │   ├── get_file_size.py
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── prepare_files.py
│   │   │   │   ├── preparer.py
│   │   │   │   └── update_checker.py
│   │   │   └── prepare_system
│   │   │       ├── config.py
│   │   │       ├── exceptions.py
│   │   │       ├── __init__.py
│   │   │       ├── models.py
│   │   │       └── preparer.py
│   │   ├── process_data
│   │   │   ├── calculate_workers_to_split_trembl_file.py
│   │   │   ├── create_trembl_iterator_partial.py
│   │   │   ├── exceptions.py
│   │   │   ├── __init__.py
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
│   │   │   ├── stick_iterators_to_tables.py
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
