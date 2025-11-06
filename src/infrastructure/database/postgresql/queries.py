from domain.entities import Tables

# Clean memory from table data and indexes.
TRUNCATE_ALL_TABLES_QUERY: str = f"""
                                 TRUNCATE TABLE
                                 {Tables.METADATA},
                                 {Tables.TAXONOMY},
                                 {Tables.LINEAGE},
                                 {Tables.UNIPROT}
                                 CASCADE
                                 """

DROP_TYPE_SOURCE_QUERY: str = """DROP TYPE IF EXISTS sequence_source CASCADE"""

DROP_IDXS_QUERY: tuple = (
    f"""DROP INDEX IF EXISTS ncbi_organism_id_{Tables.UNIPROT}_idx""",
    f"""DROP INDEX IF EXISTS {Tables.UNIPROT}_source_idx""",
    """DROP INDEX IF EXISTS trgm_sequence_idx""",
    f"""DROP INDEX IF EXISTS {Tables.UNIPROT}_pkey_idx""",
    f"""DROP INDEX IF EXISTS {Tables.TAXONOMY}_pkey_idx""",
    """DROP INDEX IF EXISTS unique_tax_name_idx""",
    f"""DROP INDEX IF EXISTS taxon_{Tables.LINEAGE}_idpair_pkey_idx""",
    f"""DROP INDEX IF EXISTS unique_taxon_{Tables.LINEAGE}_idpair_idx""",
)

# Create extension to create gin index on sequence later.
CREATE_TRGM_EXTENSION_QUERY: str = """CREATE EXTENSION IF NOT EXISTS pg_trgm"""

# If uniprot_kb exist already and we need to update -
# drop all constraints and clean all the tables.
DROP_CONSTRAINTS_UNIPROT_KB_QUERY: str = f"""
                                         ALTER TABLE IF EXISTS {Tables.UNIPROT}
                                         DROP CONSTRAINT IF EXISTS {Tables.UNIPROT}_pkey
                                         """

DROP_CONSTRAINTS_TAXONOMY_QUERY: str = f"""
                               ALTER TABLE IF EXISTS {Tables.TAXONOMY}
                               DROP CONSTRAINT IF EXISTS {Tables.TAXONOMY}_pkey CASCADE,
                               DROP CONSTRAINT IF EXISTS unique_tax_name
                               """

DROP_CONSTRAINTS_LINEAGE_QUERY: str = f"""
    ALTER TABLE IF EXISTS {Tables.LINEAGE}
    DROP CONSTRAINT IF EXISTS taxon_{Tables.LINEAGE}_idpair_pkey,
    DROP CONSTRAINT IF EXISTS unique_taxon_{Tables.LINEAGE}_idpair
    """

# Create all tables without constraints to load data faster.
DROP_METADATA_QUERY: str = f"""DROP TABLE IF EXISTS {Tables.METADATA} CASCADE"""

CREATE_METADATA_QUERY: str = f"""
                             CREATE TABLE IF NOT EXISTS {Tables.METADATA}(
                             data_source VARCHAR(100),
                             data_license VARCHAR(100),
                             license_url VARCHAR(250),
                             attribution_required VARCHAR(3)
                             )
                             """
DROP_TAXONOMY_QUERY: str = f"""DROP TABLE IF EXISTS {Tables.TAXONOMY} CASCADE"""

CREATE_TAXONOMY_QUERY: str = f"""
                             CREATE TABLE IF NOT EXISTS {Tables.TAXONOMY}(
                             rank VARCHAR(60),
                             ncbi_taxon_id INT,
                             tax_name VARCHAR(1000))
                             """

DROP_LINEAGE_QUERY: str = f"""DROP TABLE IF EXISTS {Tables.LINEAGE} CASCADE"""

CREATE_LINEAGE_QUERY: str = f"""
                            CREATE TABLE IF NOT EXISTS {Tables.LINEAGE}(
                            ncbi_taxon_id INT,
                            ncbi_lineage_id INT)
                            """

DROP_MERGED_ID_QUERY: str = f"""DROP TABLE IF EXISTS {Tables.MERGED} CASCADE"""

CREATE_MERGED_ID_QUERY: str = f"""
                              CREATE TABLE IF NOT EXISTS {Tables.MERGED}(
                              deprecated_ncbi_taxon_id INT,
                              current_ncbi_taxon_id INT
                              )
                              """

CREATE_SOURCE_ENUM_QUERY: str = """
                                CREATE TYPE sequence_source AS ENUM(
                                 'sp',
                                 'tr',
                                 'sp_iso',
                                 'tr_iso'
                                )
                                """

DROP_UNIPROT_KB_QUERY: str = f"""DROP TABLE IF EXISTS {Tables.UNIPROT} CASCADE"""

CREATE_UNIPROT_KB_QUERY: str = f"""
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

CREATE_TAXONOMY_TAX_NAME_IDX_QUERY: str = f"""
                                            CREATE UNIQUE INDEX unique_tax_name_idx
                                            ON {Tables.TAXONOMY} (tax_name)
                                            """

ADD_CONSTRAINTS_TAXONOMY_QUERY: str = f"""
                                      ALTER TABLE {Tables.TAXONOMY}
                                      ADD CONSTRAINT taxonomy_pkey
                                      PRIMARY KEY (ncbi_taxon_id),
                                      ADD CONSTRAINT unique_tax_name
                                      UNIQUE USING INDEX unique_tax_name_idx
                                      """

ADD_NOT_NULL_CONSTRAINT_TAXONOMY_QUERY: str = f"""
                                              ALTER TABLE {Tables.TAXONOMY}
                                              ALTER COLUMN rank SET NOT NULL,
                                              ALTER COLUMN tax_name SET NOT NULL
                                              """

# Create indexes temporarily for faster performance.
CREATE_TMP_IDXS_QUERY: tuple = (
    f"""CREATE INDEX IF NOT EXISTS {Tables.MERGED}_tmp_current_ncbi_taxon_id
        ON {Tables.MERGED} (current_ncbi_taxon_id)""",
    f"""CREATE INDEX IF NOT EXISTS {Tables.MERGED}_tmp_deprecated_ncbi_taxon_id
        ON {Tables.MERGED} (deprecated_ncbi_taxon_id)""",
    f"""CREATE INDEX IF NOT EXISTS {Tables.UNIPROT}_tmp_ncbi_organism_id
        ON {Tables.UNIPROT} (ncbi_organism_id)""",
)

# Find all deprecated ncbi IDs from uniprot tables and substitute them with current ones
# using table 'merged_id'.
SUBSTITUTE_OUTDATED_NCBI_IDS_IN_UNIPROT_KB_QUERY: str = f"""
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
CREATE_NCBI_ID_FKEY_UNIPROT_KB: str = f"""
    ALTER TABLE {Tables.UNIPROT}
    ADD CONSTRAINT {Tables.UNIPROT}_ncbi_organism_id_fkey
    FOREIGN KEY (ncbi_organism_id)
    REFERENCES {Tables.TAXONOMY} (ncbi_taxon_id)
    ON UPDATE CASCADE
    """

# Add not null constraints to uniprot_kb.
ADD_NOT_NULL_UNIPROT_KB_QUERY: str = f"""
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
DROP_UNUSED_IDXS_QUERY: tuple = (
    f"""DROP INDEX IF EXISTS {Tables.MERGED}_tmp_current_ncbi_taxon_id""",
    f"""DROP INDEX IF EXISTS {Tables.MERGED}_tmp_deprecated_ncbi_taxon_id""",
    f"""DROP INDEX IF EXISTS {Tables.UNIPROT}_tmp_ncbi_organism_id""",
)

ADD_PK_CONSTRAINT_UNIPROT_KB_QUERY: str = f"""
                                     ALTER TABLE {Tables.UNIPROT}
                                     ADD CONSTRAINT {Tables.UNIPROT}_pkey
                                     PRIMARY KEY (accession)
                                     """

CREATE_IDXS_UNIPROT_KB_QUERY: tuple = (
    f"""CREATE INDEX IF NOT EXISTS ncbi_organism_id_{Tables.UNIPROT}_idx
        ON {Tables.UNIPROT} (ncbi_organism_id)""",
    f"""CREATE INDEX IF NOT EXISTS {Tables.UNIPROT}_source ON {Tables.UNIPROT} (source)
        WHERE source != 'tr'""",
)

CREATE_LINEAGE_IDXS_QUERY: str = f"""
                             CREATE UNIQUE INDEX unique_taxon_{Tables.LINEAGE}_idpair
                             ON {Tables.LINEAGE} (ncbi_lineage_id, ncbi_taxon_id)
                             """

ADD_CONSTRAINTS_LINEAGE_QUERY: str = f"""
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

ADD_NOT_NULL_CONSTRAINTS_LINEAGE_QUERY: str = f"""
                                              ALTER TABLE {Tables.LINEAGE}
                                              ALTER COLUMN ncbi_taxon_id SET NOT NULL,
                                              ALTER COLUMN ncbi_lineage_id SET NOT NULL
                                              """

# Database comments.
UNIPROT_KB_COMMENTS_QUERY: tuple = (
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

TAXONOMY_COMMENTS_QUERY: tuple = (
    f"COMMENT ON TABLE {Tables.TAXONOMY} is 'Taxonomy info.'",
    f"COMMENT ON COLUMN {Tables.TAXONOMY}.ncbi_taxon_id is 'NCBI taxon ID, PK.'",
    f"COMMENT ON COLUMN {Tables.TAXONOMY}.tax_name is 'Taxon name with NCBI taxon ID.'",
    f"COMMENT ON COLUMN {Tables.TAXONOMY}.rank is 'Rank of the taxon.'",
)

LINEAGE_COMMENTS_QUERY: tuple = (
    f"COMMENT ON TABLE {Tables.LINEAGE} is 'Lineage taxons that correspond organism.'",
    f"COMMENT ON COLUMN {Tables.LINEAGE}.ncbi_taxon_id is "
    "'NCBI taxon ID of the organism that posess lineage taxons FK.'",
    f"COMMENT ON COLUMN {Tables.LINEAGE}.ncbi_lineage_id is "
    "'NCBI lineage taxon ID that are possessed by organism FK.'",
)

INSERT_INFO_INTO_METADATA: str = f"""
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

CREATE_TRGM_IDX_ON_TAXONOMY: str = f"""CREATE INDEX trgm_tax_name_idx ON
                                         {Tables.TAXONOMY}
                                         USING GIN(tax_name gin_trgm_ops)
                                     """

REMOVE_DATABASE_QUERIES: tuple = (
    DROP_TYPE_SOURCE_QUERY,
    DROP_IDXS_QUERY,
    DROP_CONSTRAINTS_UNIPROT_KB_QUERY,
    DROP_CONSTRAINTS_TAXONOMY_QUERY,
    DROP_CONSTRAINTS_LINEAGE_QUERY,
    DROP_METADATA_QUERY,
    DROP_UNIPROT_KB_QUERY,
    DROP_TAXONOMY_QUERY,
    DROP_LINEAGE_QUERY,
    DROP_MERGED_ID_QUERY,
)

RESET_DATABASE_QUERIES: tuple = (
    TRUNCATE_ALL_TABLES_QUERY,
    REMOVE_DATABASE_QUERIES,
)

PREPARATION_QUERIES: tuple = (
    CREATE_TRGM_EXTENSION_QUERY,
    CREATE_SOURCE_ENUM_QUERY,
)

TABLE_CREATION_QUERIES: tuple = (
    CREATE_METADATA_QUERY,
    CREATE_UNIPROT_KB_QUERY,
    CREATE_MERGED_ID_QUERY,
    CREATE_TAXONOMY_QUERY,
    CREATE_LINEAGE_QUERY,
)

COMMENT_QUERIES: tuple = (
    UNIPROT_KB_COMMENTS_QUERY,
    TAXONOMY_COMMENTS_QUERY,
    LINEAGE_COMMENTS_QUERY,
    INSERT_INFO_INTO_METADATA,
)

TAXONOMY_CREATE_CONSTRAINTS_AND_IDXS_QUERIES: tuple = (
    CREATE_TAXONOMY_TAX_NAME_IDX_QUERY,
    ADD_CONSTRAINTS_TAXONOMY_QUERY,
    ADD_NOT_NULL_CONSTRAINT_TAXONOMY_QUERY,
    CREATE_TRGM_IDX_ON_TAXONOMY,
)

LINEAGE_CREATE_CONSTRAINTS_AND_IDXS_QUERIES: tuple = (
    CREATE_LINEAGE_IDXS_QUERY,
    ADD_CONSTRAINTS_LINEAGE_QUERY,
    ADD_NOT_NULL_CONSTRAINTS_LINEAGE_QUERY,
)

CREATE_CONSTRAINTS_AND_IDXS_FOR_TAXONOMY_AND_LINEAGE_QUERIES: tuple = (
    TAXONOMY_CREATE_CONSTRAINTS_AND_IDXS_QUERIES,
    LINEAGE_CREATE_CONSTRAINTS_AND_IDXS_QUERIES,
)

UNIPROT_KB_AND_TAXONOMY_VALIDATION_QUERIES: tuple = (
    SUBSTITUTE_OUTDATED_NCBI_IDS_IN_UNIPROT_KB_QUERY,
    CREATE_NCBI_ID_FKEY_UNIPROT_KB,
    ADD_NOT_NULL_UNIPROT_KB_QUERY,
    DROP_UNUSED_IDXS_QUERY,
    DROP_MERGED_ID_QUERY,
    ADD_PK_CONSTRAINT_UNIPROT_KB_QUERY,
    CREATE_IDXS_UNIPROT_KB_QUERY,
)
