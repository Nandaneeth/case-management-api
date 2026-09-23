"""REST API source reader for JSON-array responses."""

from __future__ import annotations

import httpx
import pandas as pd

from etl.ingestion.source_reader import SourceReader


class ApiReader(SourceReader):
	"""Read a JSON array from a REST API into a Pandas DataFrame."""

	def __init__(self, api_url: str, timeout: float = 10.0):
		if not api_url.strip():
			raise ValueError("API URL must not be empty.")
		if timeout <= 0:
			raise ValueError("API timeout must be greater than zero.")
		self.api_url = api_url
		self.timeout = timeout

	def read(self) -> pd.DataFrame:
		"""Make a GET request and parse its JSON array response."""

		try:
			response = httpx.get(self.api_url, timeout=self.timeout)
			response.raise_for_status()
		except httpx.HTTPStatusError as error:
			raise RuntimeError(
				f"API request failed with HTTP {error.response.status_code}: "
				f"{self.api_url}"
			) from error
		except httpx.RequestError as error:
			raise RuntimeError(f"API request could not be completed: {self.api_url}") from error

		payload = response.json()
		if not isinstance(payload, list):
			raise ValueError("API response must be a JSON array of records.")

		return pd.DataFrame(payload)


def read_api(api_url: str, timeout: float = 10.0) -> pd.DataFrame:
	"""Read a JSON array response from a configurable REST API URL."""

	return ApiReader(api_url, timeout).read()
