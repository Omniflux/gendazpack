from abc import ABC, abstractmethod
from re import search, IGNORECASE
from typing import Any, Self
from urllib.parse import ParseResult, urlparse

from keyring import get_credential, set_password

from ..generator import PackageData

credential_service_name = 'gendazpack'

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
	def scrape(url: ParseResult, auth: list[str] | None) -> PackageData:
		raise NotImplementedError

def get_scraper(url: ParseResult | None) -> type[Scraper] | None:
	if url and url.hostname:
		if url.hostname == 'web.archive.org' and (suburl := search('(https?://.*)', url.path, IGNORECASE)):
			url = urlparse(suburl.group(0))

		if url.hostname and (site := url.hostname.split("www.")[-1]) in Scraper.scrapers:
			return Scraper.scrapers[site]
		else:
			raise ValueError(f'No scraper for site: {url.hostname}')

def scrape(url: ParseResult, auth: list[str] | None, save_auth: bool) -> PackageData:
	try:
		if scraper := get_scraper(url):
			if auth and save_auth:
				set_password(f"{credential_service_name} - {scraper.domain}", *auth)

			if not auth and (credentials := get_credential(f"{credential_service_name} - {scraper.domain}", None)):
				auth = [credentials.username, credentials.password]

			return scraper.scrape(url, auth)
	except ValueError:
		pass

	return PackageData()
