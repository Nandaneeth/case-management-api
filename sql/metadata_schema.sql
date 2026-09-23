-- Metadata tables for the Week 2 metadata-driven ETL pipeline.
-- SQLite enforces foreign keys per connection; enable them with:
-- PRAGMA foreign_keys = ON;

CREATE TABLE table_metadata (
    table_metadata_id INTEGER PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_table_name TEXT NOT NULL,
    target_table_name TEXT NOT NULL,
    source_path TEXT NOT NULL,
    file_format TEXT NOT NULL CHECK (file_format IN ('csv', 'parquet', 'json')),
    target_layer TEXT NOT NULL CHECK (target_layer IN ('bronze', 'silver', 'gold')),
    target_path TEXT NOT NULL,
    active_flag INTEGER NOT NULL DEFAULT 1 CHECK (active_flag IN (0, 1)),
    UNIQUE (source_system, source_table_name),
    UNIQUE (target_table_name)
);

CREATE TABLE column_mapping (
    column_mapping_id INTEGER PRIMARY KEY,
    table_metadata_id INTEGER NOT NULL,
    source_column_name TEXT NOT NULL,
    target_column_name TEXT NOT NULL,
    target_data_type TEXT NOT NULL,
    mapping_type TEXT NOT NULL DEFAULT 'rename'
        CHECK (mapping_type IN ('direct', 'rename', 'derived')),
    transformation_rule TEXT,
    UNIQUE (table_metadata_id, source_column_name),
    UNIQUE (table_metadata_id, target_column_name),
    FOREIGN KEY (table_metadata_id)
        REFERENCES table_metadata (table_metadata_id)
        ON DELETE CASCADE
);

CREATE TABLE scd2_rules (
    scd2_rule_id INTEGER PRIMARY KEY,
    table_metadata_id INTEGER NOT NULL,
    target_table_name TEXT NOT NULL,
    business_key_column TEXT NOT NULL,
    change_detection_columns TEXT NOT NULL,
    effective_start_column TEXT NOT NULL,
    effective_end_column TEXT NOT NULL,
    current_flag_column TEXT NOT NULL,
    UNIQUE (table_metadata_id),
    UNIQUE (target_table_name),
    FOREIGN KEY (table_metadata_id)
        REFERENCES table_metadata (table_metadata_id)
        ON DELETE CASCADE
);
