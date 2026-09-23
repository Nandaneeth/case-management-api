"""Tests for the metadata-only ETL configuration reader."""

import sqlite3

import pytest

from etl.metadata.reader import MetadataReader, MetadataValidationError


class _FakeDataFrame:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0]

    def collect(self):
        return self._rows


class _FakeSpark:
    def createDataFrame(self, rows, _schema):
        return _FakeDataFrame(rows)


@pytest.fixture()
def spark():
    return _FakeSpark()


@pytest.fixture()
def metadata_database(tmp_path):
    database_path = tmp_path / "metadata.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE table_metadata (
                table_metadata_id INTEGER PRIMARY KEY,
                source_system TEXT NOT NULL,
                source_table_name TEXT NOT NULL,
                target_table_name TEXT NOT NULL,
                source_path TEXT NOT NULL,
                file_format TEXT NOT NULL,
                target_layer TEXT NOT NULL,
                target_path TEXT NOT NULL,
                active_flag INTEGER NOT NULL
            );
            CREATE TABLE column_mapping (
                column_mapping_id INTEGER PRIMARY KEY,
                table_metadata_id INTEGER NOT NULL,
                source_column_name TEXT NOT NULL,
                target_column_name TEXT NOT NULL,
                target_data_type TEXT NOT NULL,
                mapping_type TEXT NOT NULL,
                transformation_rule TEXT
            );
            CREATE TABLE scd2_rules (
                scd2_rule_id INTEGER PRIMARY KEY,
                table_metadata_id INTEGER NOT NULL,
                target_table_name TEXT NOT NULL,
                business_key_column TEXT NOT NULL,
                change_detection_columns TEXT NOT NULL,
                effective_start_column TEXT NOT NULL,
                effective_end_column TEXT NOT NULL,
                current_flag_column TEXT NOT NULL
            );
            INSERT INTO table_metadata VALUES
                (1, 'case_api', 'cases', 'silver_cases',
                 'data/source/cases.csv', 'csv', 'silver',
                 'data/silver/cases', 1);
            INSERT INTO column_mapping VALUES
                (1, 1, 'case_number', 'case_number', 'string', 'direct', NULL);
            INSERT INTO scd2_rules VALUES
                (1, 1, 'silver_cases', 'case_number', 'status, priority',
                 'effective_from', 'effective_to', 'is_current');
            """
        )
    return database_path


def test_reads_structured_active_configuration(spark, metadata_database):
    configuration = MetadataReader(spark, metadata_database).read(1)

    assert configuration.table.source_table_name == "cases"
    assert configuration.table.source_path == "data/source/cases.csv"
    assert configuration.column_mappings[0].target_column_name == "case_number"
    assert configuration.scd2_rule.change_detection_columns == ("status", "priority")


def test_rejects_missing_table_metadata(spark, metadata_database):
    with pytest.raises(MetadataValidationError, match="was not found"):
        MetadataReader(spark, metadata_database).read(99)


def test_rejects_missing_column_mappings(spark, metadata_database):
    with sqlite3.connect(metadata_database) as connection:
        connection.execute("DELETE FROM column_mapping")

    with pytest.raises(MetadataValidationError, match="no column mappings"):
        MetadataReader(spark, metadata_database).read(1)