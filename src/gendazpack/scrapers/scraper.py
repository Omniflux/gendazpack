from abc import ABC, abstractmethod
from re import search, IGNORECASE
from typing import Any, Self
from urllib.parse import ParseResult, urlparse

from ..generator import PackageData

class Scraper(ABC):
	domain: str
	scrapers: dict[str, type[Self]] = {}

	def __init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
		if not hasattr(cls, 'domain'):
			raise TypeError(f'{cls.__name__}.domain must be set.')
		super().__init_subclass__(**kwargs)
		cls.scrapers[cls.domain] = cls

	@staticmethod
	@abstractmethod
	def scrape(url: ParseResult) -> PackageData:
		raise NotImplementedError

def get_scraper(url: ParseResult | None) -> type[Scraper] | None:
	if url and url.hostname:
		if url.hostname == 'web.archive.org' and (suburl := search('(https?://.*)', url.path, IGNORECASE)):
			url = urlparse(suburl.group(0))

		if url.hostname and (site := url.hostname.split("www.")[-1]) in Scraper.scrapers:
			return Scraper.scrapers[site]
		else:
			raise ValueError(f'No scraper for site: {url.hostname}')

def scrape(url: ParseResult) -> PackageData:
	try:
		if scraper := get_scraper(url):
			return scraper.scrape(url)
	except ValueError:
		pass

	return PackageData()