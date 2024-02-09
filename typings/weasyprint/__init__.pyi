from collections.abc import Callable
from pathlib import Path
from ssl import SSLContext
from typing import Any, BinaryIO, TextIO, overload

from cssselect2 import Matcher
from pydyf import PDF

from .css.counters import CounterStyle
from .text.document import Document
from .text.fonts import FontConfiguration
from .urls import default_url_fetcher

class HTML:
	def __init__(self,
		guess: Any = None,
		filename: Path | str | None = None,
		url: str | None = None,
		file_obj: BinaryIO | TextIO | None = None,
		string: str | None = None,
		encoding: str | None = None,
	    base_url: str | None = None,
		url_fetcher: Callable[[str, int, SSLContext | None], dict[str, Any]] | None = default_url_fetcher,
		media_type: str | None = 'print',
	) -> None:
		...

	@overload
	def write_pdf(self,
		target: None = None,
		zoom: float = 1,
		finisher: Callable[[Document, PDF], None] | None = None,
		font_config: FontConfiguration | None = None,
		counter_style: CounterStyle | None = None,
		**options: Any | None
	) -> bytes:
		...

	@overload
	def write_pdf(self,
		target: str | Path | BinaryIO | TextIO,
		zoom: float = 1,
		finisher: Callable[[Document, PDF], None] | None = None,
		font_config: FontConfiguration | None = None,
		counter_style: CounterStyle | None = None,
		**options: Any | None
	) -> None:
		...

class CSS:
	def __init__(self,
		guess: Any = None,
		filename: Path | str | None = None,
		url: str | None = None,
		file_obj: BinaryIO | TextIO | None = None,
		string: str | None = None,
		encoding: str | None = None,
	    base_url: str | None = None,
		url_fetcher: Callable[[str, int, SSLContext | None], dict[str, Any]] | None = default_url_fetcher,
		_check_mime_type: bool = False,
		media_type: str | None = 'print',
		font_config: FontConfiguration | None = None,
		counter_style: CounterStyle | None = None,
        matcher: Matcher | None = None,
		page_rules: Any | None = None
	) -> None:
		...