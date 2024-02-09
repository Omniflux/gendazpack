from ssl import SSLContext
from typing import Any, AnyStr, IO

def default_url_fetcher(url: str, timeout: int = 10, ssl_context: SSLContext | None = None) -> dict[str, Any]:
	...

class StreamingGzipFile:
	def __init__(self, fileobj: IO[AnyStr]) -> None:
		...