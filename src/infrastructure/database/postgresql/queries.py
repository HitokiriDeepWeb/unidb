from domain.entities import Tables

# Clean memory from table data and indexes.
_TRUNCATE_ALL_TABLES_QUERY: str = f"""
                                 TRUNCATE TABLE
                                 {Tables.METADATA},
                                 {Tables.TAXONOMY},
                                 {Tables.LINEAGE},
                                 {Tables.UNIPROT}
                                 CASCADE
                                 """

_DROP_TYPE_SOURCE_QUERY: str = "DROP TYPE IF EXISTS sequence_source CASCADE"

_DROP_IDXS_QUERY: tuple = (
    f"DROP INDEX IF EXISTS ncbi_organism_id_{Tables.UNIPROT}_idx",
    f"DROP INDEX IF EXISTS {Tables.UNIPROT}_source_idx",
    "DROP INDEX IF EXISTS trgm_sequence_idx",
    f"DROP INDEX IF EXISTS {Tables.UNIPROT}_pkey_idx",
    f"DROP INDEX IF EXISTS {Tables.TAXONOMY}_pkey_idx",
    "DROP INDEX IF EXISTS unique_tax_name_idx",
    f"DROP INDEX IF EXISTS taxon_{Tables.LINEAGE}_idpair_pkey_idx",
    f"DROP INDEX IF EXISTS unique_taxon_{Tables.LINEAGE}_idpair_idx",
)

# Create extension to create gin index on sequence later.
_CREATE_TRGM_EXTENSION_QUERY: str = "CREATE EXTENSION IF NOT EXISTS pg_trgm"

# If uniprot_kb exist already and we need to update -
# drop all constraints and clean all the tables.
_DROP_CONSTRAINTS_UNIPROT_KB_QUERY: str = f"""
                                         ALTER TABLE IF EXISTS {Tables.UNIPROT}
                                         DROP CONSTRAINT IF EXISTS {Tables.UNIPROT}_pkey
                                         """

_DROP_CONSTRAINTS_TAXONOMY_QUERY: str = f"""
                               ALTER TABLE IF EXISTS {Tables.TAXONOMY}
                               DROP CONSTRAINT IF EXISTS {Tables.TAXONOMY}_pkey CASCADE,
                               DROP CONSTRAINT IF EXISTS unique_tax_name
                               """

_DROP_CONSTRAINTS_LINEAGE_QUERY: str = f"""
    ALTER TABLE IF EXISTS {Tables.LINEAGE}
    DROP CONSTRAINT IF EXISTS taxon_{Tables.LINEAGE}_idpair_pkey,
    DROP CONSTRAINT IF EXISTS unique_taxon_{Tables.LINEAGE}_idpair
    """

# Create all tables without constraints to load data faster.
_DROP_METADATA_QUERY: str = f"""DROP TABLE IF EXISTS {Tables.METADATA} CASCADE"""

_CREATE_METADATA_QUERY: str = f"""
                             CREATE TABLE IF NOT EXISTS {Tables.METADATA}(
                             data_source VARCHAR(100),
                             data_license VARCHAR(100),
                             license_url VARCHAR(250),
                             attribution_required VARCHAR(3)
                             )
                             """
_DROP_TAXONOMY_QUERY: str = f"DROP TABLE IF EXISTS {Tables.TAXONOMY} CASCADE"

_CREATE_TAXONOMY_QUERY: str = f"""
                             CREATE TABLE IF NOT EXISTS {Tables.TAXONOMY}(
                             rank VARCHAR(60),
                             ncbi_taxon_id INT,
                             tax_name VARCHAR(1000))
                             """

_DROP_LINEAGE_QUERY: str = f"DROP TABLE IF EXISTS {Tables.LINEAGE} CASCADE"

_CREATE_LINEAGE_QUERY: str = f"""
                            CREATE TABLE IF NOT EXISTS {Tables.LINEAGE}(
                            ncbi_taxon_id INT,
                            ncbi_lineage_id INT)
                            """

_DROP_MERGED_ID_QUERY: str = f"DROP TABLE IF EXISTS {Tables.MERGED} CASCADE"

_CREATE_MERGED_ID_QUERY: str = f"""
                              CREATE TABLE IF NOT EXISTS {Tables.MERGED}(
                              deprecated_ncbi_taxon_id INT,
                              current_ncbi_taxon_id INT
                              )
                              """

_CREATE_SOURCE_ENUM_QUERY: str = """
                                CREATE TYPE sequence_source AS ENUM(
                                 'sp',
                                 'tr',
                                 'sp_iso',
                                 'tr_iso'
                                )
                                """

_DROP_UNIPROT_KB_QUERY: str = f"DROP TABLE IF EXISTS {Tables.UNIPROT} CASCADE"

_CREATE_UNIPROT_KB_QUERY: str = f"""
                               CREATE TABLE IF NOT EXISTS {Tables.UNIPROT}(
                               source sequence_source,
                               is_reviewed bool,
                               accession VARCHAR(13),
                               entry_name VARCHAR(20),
                               peptide_name VARCHAR(500),
                               ncbi_organism_id INT,
                               organism_name VARCHAR(500),
                               sequence TEXT)
                               """

_CREATE_TAXONOMY_TAX_NAME_IDX_QUERY: str = f"""
                                            CREATE UNIQUE INDEX unique_tax_name_idx
                                            ON {Tables.TAXONOMY} (tax_name)
                                            """

_ADD_CONSTRAINTS_TAXONOMY_QUERY: str = f"""
                                      ALTER TABLE {Tables.TAXONOMY}
                                      ADD CONSTRAINT taxonomy_pkey
                                      PRIMARY KEY (ncbi_taxon_id),
                                      ADD CONSTRAINT unique_tax_name
                                      UNIQUE USING INDEX unique_tax_name_idx
                                      """

_ADD_NOT_NULL_CONSTRAINT_TAXONOMY_QUERY: str = f"""
                                              ALTER TABLE {Tables.TAXONOMY}
                                              ALTER COLUMN rank SET NOT NULL,
                                              ALTER COLUMN tax_name SET NOT NULL
                                              """

# Create indexes temporarily for faster performance.
_CREATE_TMP_IDXS_QUERY: tuple = (
    f"""CREATE INDEX IF NOT EXISTS {Tables.MERGED}_tmp_current_ncbi_taxon_id
        ON {Tables.MERGED} (current_ncbi_taxon_id)""",
    f"""CREATE INDEX IF NOT EXISTS {Tables.MERGED}_tmp_deprecated_ncbi_taxon_id
        ON {Tables.MERGED} (deprecated_ncbi_taxon_id)""",
    f"""CREATE INDEX IF NOT EXISTS {Tables.UNIPROT}_tmp_ncbi_organism_id
        ON {Tables.UNIPROT} (ncbi_organism_id)""",
)

# Find all deprecated ncbi IDs from uniprot tables and substitute them with current ones
# using table 'merged_id'.
_SUBSTITUTE_OUTDATED_NCBI_IDS_IN_UNIPROT_KB_QUERY: str = f"""
        UPDATE {Tables.UNIPROT}
        SET ncbi_organism_id = current_ncbi_taxon_id
        FROM {Tables.MERGED}
        WHERE deprecated_ncbi_taxon_id in
            (SELECT ncbi_organism_id
             FROM {Tables.UNIPROT}
             INTERSECT
             SELECT deprecated_ncbi_taxon_id
             FROM {Tables.MERGED})
        AND ncbi_organism_id = deprecated_ncbi_taxon_id
        """

# Since ncbi ids in uniprot tables and ids from 'taxonomy' table are the same now -
# create foreign keys.
_CREATE_NCBI_ID_FKEY_UNIPROT_KB: str = f"""
    ALTER TABLE {Tables.UNIPROT}
    ADD CONSTRAINT {Tables.UNIPROT}_ncbi_organism_id_fkey
    FOREIGN KEY (ncbi_organism_id)
    REFERENCES {Tables.TAXONOMY} (ncbi_taxon_id)
    ON UPDATE CASCADE
    """

# Add not null constraints to uniprot_kb.
_ADD_NOT_NULL_UNIPROT_KB_QUERY: str = f"""
                                ALTER TABLE {Tables.UNIPROT}
                                ALTER COLUMN source SET NOT NULL,
                                ALTER COLUMN is_reviewed SET NOT NULL,
                                ALTER COLUMN entry_name SET NOT NULL,
                                ALTER COLUMN peptide_name SET NOT NULL,
                                ALTER COLUMN ncbi_organism_id SET NOT NULL,
                                ALTER COLUMN organism_name SET NOT NULL,
                                ALTER COLUMN sequence SET NOT NULL
                                """

# Drop indexes that we don't need anymore.
_DROP_UNUSED_IDXS_QUERY: tuple = (
    f"DROP INDEX IF EXISTS {Tables.MERGED}_tmp_current_ncbi_taxon_id",
    f"DROP INDEX IF EXISTS {Tables.MERGED}_tmp_deprecated_ncbi_taxon_id",
    f"DROP INDEX IF EXISTS {Tables.UNIPROT}_tmp_ncbi_organism_id",
)

_ADD_PK_CONSTRAINT_UNIPROT_KB_QUERY: str = f"""
                                     ALTER TABLE {Tables.UNIPROT}
                                     ADD CONSTRAINT {Tables.UNIPROT}_pkey
                                     PRIMARY KEY (accession)
                                     """

_CREATE_IDXS_UNIPROT_KB_QUERY: tuple = (
    f"""CREATE INDEX IF NOT EXISTS ncbi_organism_id_{Tables.UNIPROT}_idx
        ON {Tables.UNIPROT} (ncbi_organism_id)""",
    f"""CREATE INDEX IF NOT EXISTS {Tables.UNIPROT}_source ON {Tables.UNIPROT} (source)
        WHERE source != 'tr'""",
)

_CREATE_LINEAGE_IDXS_QUERY: str = f"""
                             CREATE UNIQUE INDEX unique_taxon_{Tables.LINEAGE}_idpair
                             ON {Tables.LINEAGE} (ncbi_lineage_id, ncbi_taxon_id)
                             """

_ADD_CONSTRAINTS_LINEAGE_QUERY: str = f"""
                              ALTER TABLE {Tables.LINEAGE}
                              ADD CONSTRAINT {Tables.LINEAGE}_ncbi_taxon_id_fkey
                              FOREIGN KEY (ncbi_taxon_id)
                              REFERENCES {Tables.TAXONOMY} (ncbi_taxon_id)
                              ON DELETE CASCADE
                              ON UPDATE CASCADE,
                              ADD CONSTRAINT {Tables.LINEAGE}_ncbi_lineage_id_fkey
                              FOREIGN KEY (ncbi_lineage_id)
                              REFERENCES {Tables.TAXONOMY} (ncbi_taxon_id)
                              ON DELETE CASCADE
                              ON UPDATE CASCADE,
                              ADD CONSTRAINT taxon_{Tables.LINEAGE}_idpair_pkey
                              PRIMARY KEY (ncbi_taxon_id, ncbi_lineage_id),
                              ADD CONSTRAINT unique_taxon_{Tables.LINEAGE}_idpair
                              UNIQUE USING INDEX unique_taxon_{Tables.LINEAGE}_idpair
                              """

_ADD_NOT_NULL_CONSTRAINTS_LINEAGE_QUERY: str = f"""
                                              ALTER TABLE {Tables.LINEAGE}
                                              ALTER COLUMN ncbi_taxon_id SET NOT NULL,
                                              ALTER COLUMN ncbi_lineage_id SET NOT NULL
                                              """

# Database comments.
_UNIPROT_KB_COMMENTS_QUERY: tuple = (
    f"COMMENT ON TABLE {Tables.UNIPROT} is "
    "'All peptide records (Swiss-Prot, TrEMBL, reviewed isoforms).'",
    f"COMMENT ON COLUMN {Tables.UNIPROT}.source is "
    "'Source sequence was added from (Swiss-Prot/TrEMBL/reviewed isoforms).'",
    f"COMMENT ON COLUMN {Tables.UNIPROT}.is_reviewed is "
    "'Was sequences reviewed manually.'",
    f"COMMENT ON COLUMN {Tables.UNIPROT}.accession is 'Sequence ID, PK.'",
    f"COMMENT ON COLUMN {Tables.UNIPROT}.entry_name is "
    "'Former sequence ID with biological info.'",
    f"COMMENT ON COLUMN {Tables.UNIPROT}.peptide_name is 'Peptide name.'",
    f"COMMENT ON COLUMN {Tables.UNIPROT}.ncbi_organism_id is "
    "'ID of the organism that possess this peptide, FK.'",
    f"COMMENT ON COLUMN {Tables.UNIPROT}.organism_name is "
    "'Organism name that possess this peptide.'",
    f"COMMENT ON COLUMN {Tables.UNIPROT}.sequence is 'Peptide sequence itself.'",
)

_TAXONOMY_COMMENTS_QUERY: tuple = (
    f"COMMENT ON TABLE {Tables.TAXONOMY} is 'Taxonomy info.'",
    f"COMMENT ON COLUMN {Tables.TAXONOMY}.ncbi_taxon_id is 'NCBI taxon ID, PK.'",
    f"COMMENT ON COLUMN {Tables.TAXONOMY}.tax_name is 'Taxon name with NCBI taxon ID.'",
    f"COMMENT ON COLUMN {Tables.TAXONOMY}.rank is 'Rank of the taxon.'",
)

_LINEAGE_COMMENTS_QUERY: tuple = (
    f"COMMENT ON TABLE {Tables.LINEAGE} is 'Lineage taxons that correspond organism.'",
    f"COMMENT ON COLUMN {Tables.LINEAGE}.ncbi_taxon_id is "
    "'NCBI taxon ID of the organism that posess lineage taxons FK.'",
    f"COMMENT ON COLUMN {Tables.LINEAGE}.ncbi_lineage_id is "
    "'NCBI lineage taxon ID that are possessed by organism FK.'",
)

_INSERT_INFO_INTO_METADATA: str = f"""
               INSERT INTO {Tables.METADATA}(data_source,
                                             data_license,
                                             license_url,
                                             attribution_required) VALUES
               ('UniProt Knowledgebase FTP', 'CC BY 4.0',
                'https://creativecommons.org/licenses/by/4.0/', 'Yes'),

               ('NCBI FTP', 'Public unrestricted scientific data',
                'https://www.ncbi.nlm.nih.gov/home/about/policies/', 'Yes')
               """

# WARNING! This index will have very large size.
CREATE_TRGM_IDX_ON_UNIPROT_KB: str = f"""CREATE INDEX trgm_sequence_idx ON
                                           {Tables.UNIPROT}
                                           USING GIN(sequence gin_trgm_ops)
                                       """

_CREATE_TRGM_IDX_ON_TAXONOMY: str = f"""CREATE INDEX trgm_tax_name_idx ON
                                         {Tables.TAXONOMY}
                                         USING GIN(tax_name gin_trgm_ops)
                                     """

REMOVE_DATABASE_QUERIES: tuple = (
    _DROP_TYPE_SOURCE_QUERY,
    _DROP_IDXS_QUERY,
    _DROP_CONSTRAINTS_UNIPROT_KB_QUERY,
    _DROP_CONSTRAINTS_TAXONOMY_QUERY,
    _DROP_CONSTRAINTS_LINEAGE_QUERY,
    _DROP_METADATA_QUERY,
    _DROP_UNIPROT_KB_QUERY,
    _DROP_TAXONOMY_QUERY,
    _DROP_LINEAGE_QUERY,
    _DROP_MERGED_ID_QUERY,
)

RESET_DATABASE_QUERIES: tuple = (
    _TRUNCATE_ALL_TABLES_QUERY,
    REMOVE_DATABASE_QUERIES,
)

PREPARATION_QUERIES: tuple = (
    _CREATE_TRGM_EXTENSION_QUERY,
    _CREATE_SOURCE_ENUM_QUERY,
)

TABLE_CREATION_QUERIES: tuple = (
    _CREATE_METADATA_QUERY,
    _CREATE_UNIPROT_KB_QUERY,
    _CREATE_MERGED_ID_QUERY,
    _CREATE_TAXONOMY_QUERY,
    _CREATE_LINEAGE_QUERY,
)

COMMENT_QUERIES: tuple = (
    _UNIPROT_KB_COMMENTS_QUERY,
    _TAXONOMY_COMMENTS_QUERY,
    _LINEAGE_COMMENTS_QUERY,
    _INSERT_INFO_INTO_METADATA,
)

_TAXONOMY_CREATE_CONSTRAINTS_AND_IDXS_QUERIES: tuple = (
    _CREATE_TAXONOMY_TAX_NAME_IDX_QUERY,
    _ADD_CONSTRAINTS_TAXONOMY_QUERY,
    _ADD_NOT_NULL_CONSTRAINT_TAXONOMY_QUERY,
    _CREATE_TRGM_IDX_ON_TAXONOMY,
)

_LINEAGE_CREATE_CONSTRAINTS_AND_IDXS_QUERIES: tuple = (
    _CREATE_LINEAGE_IDXS_QUERY,
    _ADD_CONSTRAINTS_LINEAGE_QUERY,
    _ADD_NOT_NULL_CONSTRAINTS_LINEAGE_QUERY,
)

CREATE_CONSTRAINTS_AND_IDXS_FOR_TAXONOMY_AND_LINEAGE_QUERIES: tuple = (
    _TAXONOMY_CREATE_CONSTRAINTS_AND_IDXS_QUERIES,
    _LINEAGE_CREATE_CONSTRAINTS_AND_IDXS_QUERIES,
)

UNIPROT_KB_AND_TAXONOMY_VALIDATION_QUERIES: tuple = (
    _SUBSTITUTE_OUTDATED_NCBI_IDS_IN_UNIPROT_KB_QUERY,
    _CREATE_NCBI_ID_FKEY_UNIPROT_KB,
    _ADD_NOT_NULL_UNIPROT_KB_QUERY,
    _DROP_UNUSED_IDXS_QUERY,
    _DROP_MERGED_ID_QUERY,
    _ADD_PK_CONSTRAINT_UNIPROT_KB_QUERY,
    _CREATE_IDXS_UNIPROT_KB_QUERY,
)
