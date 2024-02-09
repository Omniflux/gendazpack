import re

from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path
from urllib.parse import urlparse, ParseResult
from uuid import UUID

from .generator import PackageGenerator
from .scrapers.scraper import get_scraper

def _content_location(path: str) -> Path:
	try:
		if (resolved_path := Path(path).resolve(True)).is_dir():
			return resolved_path
		else:
			raise ValueError(f'{path} is not a directory')
	except Exception as e:
		raise ArgumentTypeError(e)

def _url(url_str: str) -> ParseResult:
	url = urlparse(url_str if "://" in url_str else "http://" + url_str)
	if not all((url.scheme, url.netloc)):
		raise ArgumentTypeError('Invalid URL')

	try:
		get_scraper(url)
	except ValueError as e:
		raise ArgumentTypeError(e)

	return url

def _prefix(store: str) -> str:
	if store in (reserved := ('IM', 'DZ', 'DAZ', 'DAZ3D', 'TAFI')):
		raise ArgumentTypeError(f'Invalid store: {reserved} are reserved')	

	pattern = r'[A-Z][0-9A-Z]{0,6}'
	if not re.compile(pattern).fullmatch(store):
		raise ArgumentTypeError(f'Invalid store: Must match regex: {pattern}')

	return store

def _sku(sku: str) -> int:
	try:
		int_sku = int(sku)
		if int_sku > 99999999:
			raise ValueError
		return int_sku
	except ValueError:
		raise ArgumentTypeError(f'Invalid SKU: Must be 1 - 8 digits')

def _id(id: str) -> int:
	try:
		int_id = int(id)
		if int_id > 99:
			raise ValueError
		return int_id
	except ValueError:
		raise ArgumentTypeError(f'Invalid ID: Must be 1 - 2 digits')

def _readme(file: str) -> Path:
	readme = Path(file)
	if not (readme.is_file() and readme.suffix.lower() == '.pdf'):
		raise ArgumentTypeError('ReadMe file must be a PDF')

	return readme

def _main() -> None:
	parser = ArgumentParser(description = 'Generate DAZ Studio Content Package')
	parser.add_argument('content_location', type = _content_location, help = 'Content Directory')
	parser.add_argument('-g', '--global-id', type = UUID, help = 'Product Global ID')
	parser.add_argument('-u', '--url', type = _url, help = 'URL for product information')
	parser.add_argument('-p', '--prefix', type = _prefix, help = 'Source Prefix')
	parser.add_argument('-s', '--sku', type = _sku, help = 'Product SKU')
	parser.add_argument('-I', '--id', type = _id, default = '0', help = 'Package ID')
	parser.add_argument('-S', '--store', type = str, help = 'Product Store')
	parser.add_argument('-n', '--name', type = str, help = 'Product [Part] Name')
	parser.add_argument('-t', '--tags', type = str, nargs = '+', help = 'Tags')
	parser.add_argument('-a', '--authors', type = str, nargs = '+', help = 'Authors')
	parser.add_argument('-d', '--description', type = str, help = 'Product Description')
	parser.add_argument('-i', '--image', type = Path, help = 'Product Image')
	parser.add_argument('-r', '--readme', type = _readme, help = 'Product ReadMe')
	parser.add_argument('-v', '--verbose', action = 'store_true', help = 'enable verbose output')

	args = parser.parse_args()

	package_generator = PackageGenerator(
		global_id=args.global_id,
		prefix=args.prefix,
		sku=args.sku,
		store=args.store,
		name=args.name,
		tags=args.tags,
		artists=args.authors,
		description=args.description,
		image=args.image,
		readme=args.readme,
		id=args.id,
		url=args.url,
		content_location=args.content_location,
		verbose=args.verbose)
	
	package_generator.make_package()

def _profile() -> None:  # pyright: ignore[reportUnusedFunction]
	import cProfile, pstats
	profiler = cProfile.Profile()
	profiler.enable()
	_main()
	profiler.disable()
	pstats.Stats(profiler).dump_stats('stats.profiler')
 
if __name__ == '__main__':
	# _profile()
	_main()