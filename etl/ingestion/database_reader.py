"""SQLAlchemy and Pandas reader for relational database tables."""

from __future__ import annotations

from sqlalchemy import create_engine

import pandas as pd

from etl.ingestion.source_reader import SourceReader


class DatabaseReader(SourceReader):
	"""Read one relational database table into a Pandas DataFrame."""

	def __init__(self, connection_url: str, table_name: str):
		if not connection_url.strip():
			raise ValueError("Database connection URL must not be empty.")
		if not table_name.strip():
			raise ValueError("Database table name must not be empty.")
		self.connection_url = connection_url
		self.table_name = table_name

	def read(self) -> pd.DataFrame:
		"""Read the configured table using a SQLAlchemy engine."""

		engine = create_engine(self.connection_url)
		try:
			return pd.read_sql_table(self.table_name, con=engine)
		finally:
			engine.dispose()


def read_database(connection_url: str, table_name: str) -> pd.DataFrame:
	"""Read a relational database table into a Pandas DataFrame."""

	return DatabaseReader(connection_url, table_name).read()
