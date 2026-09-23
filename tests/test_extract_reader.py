"""Tests for metadata-driven source extraction."""

from pathlib import Path

import pytest

from etl.extract.reader import ExtractionError, SourceReader
from etl.metadata.reader import (
    ColumnMapping,
    MetadataConfiguration,
    Scd2Rule,
    TableMetadata,
)


class _FakeDataFrame:
    pass


class _FakeReader:
    def __init__(self):
        self.options = {}
        self.format_name = None
        self.loaded_path = None

    def format(self, name):
        self.format_name = name
        return self

    def option(self, name, value):
        self.options[name] = value
        return self

    def load(self, path):
        self.loaded_path = path
        return _FakeDataFrame()


class _FakeSpark:
    def __init__(self):
        self.read = _FakeReader()


def _configuration(source_path: str, file_format: str = "csv"):
    return MetadataConfiguration(
        table=TableMetadata(
            table_metadata_id=1,
            source_system="case_api",
            source_table_name="cases",
            target_table_name="silver_cases",
            source_path=source_path,
            file_format=file_format,
            target_layer="silver",
            target_path="data/silver/cases",
            active_flag=True,
        ),
        column_mappings=(
            ColumnMapping("case_number", "case_number", "string", "direct", None),
        ),
        scd2_rule=Scd2Rule(
            "silver_cases",
            "case_number",
            ("status",),
            "effective_from",
            "effective_to",
            "is_current",
        ),
    )


def test_reads_csv_from_metadata_path(tmp_path: Path):
    source_path = tmp_path / "source.csv"
    source_path.write_text("case_number,title\nCASE-1,Access issue\n", encoding="utf-8")
    spark = _FakeSpark()

    result = SourceReader(spark).read(_configuration(str(source_path)))

    assert isinstance(result, _FakeDataFrame)
    assert spark.read.format_name == "csv"
    assert spark.read.options == {"header": True, "inferSchema": True}
    assert spark.read.loaded_path == str(source_path)


def test_rejects_missing_source_file(tmp_path: Path):
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(ExtractionError, match="was not found"):
        SourceReader(_FakeSpark()).read(_configuration(str(missing_path)))


def test_rejects_unsupported_source_format(tmp_path: Path):
    source_path = tmp_path / "source.json"
    source_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="Only CSV is supported"):
        SourceReader(_FakeSpark()).read(_configuration(str(source_path), "json"))