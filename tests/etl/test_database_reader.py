"""Tests for reading the existing local cases table."""

import pandas as pd

from app.core.config import settings
from etl.ingestion.database_reader import read_database


def test_reads_existing_cases_table_from_local_database() -> None:
	dataframe = read_database(settings.database_url, "cases")

	assert isinstance(dataframe, pd.DataFrame)
	assert {
		"id",
		"case_number",
		"title",
		"description",
		"status",
		"priority",
		"created_at",
		"updated_at",
	}.issubset(dataframe.columns)

	if not dataframe.empty:
		assert len(dataframe) >= 1
