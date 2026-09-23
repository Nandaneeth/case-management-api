"""Tests for Bronze Parquet writing."""

from pathlib import Path

from etl.load.writer import BronzeWriter


class _FakeWriter:
    def __init__(self):
        self.mode_name = None
        self.format_name = None
        self.saved_path = None

    def mode(self, name):
        self.mode_name = name
        return self

    def format(self, name):
        self.format_name = name
        return self

    def save(self, path):
        self.saved_path = path


class _FakeDataFrame:
    def __init__(self):
        self.write = _FakeWriter()
        self.added_column = None

    def withColumn(self, name, expression):
        self.added_column = (name, expression)
        return self

    def count(self):
        return 10


def test_writes_parquet_with_ingestion_timestamp(tmp_path: Path, caplog, monkeypatch):
    dataframe = _FakeDataFrame()
    destination = tmp_path / "bronze"
    monkeypatch.setattr("etl.load.writer.current_timestamp", lambda: "timestamp")

    with caplog.at_level("INFO"):
        result = BronzeWriter(destination).write(dataframe)

    assert result == str(destination)
    assert dataframe.added_column[0] == "ingestion_timestamp"
    assert dataframe.write.mode_name == "append"
    assert dataframe.write.format_name == "parquet"
    assert dataframe.write.saved_path == str(destination)
    assert "Wrote 10 rows to Bronze path" in caplog.text