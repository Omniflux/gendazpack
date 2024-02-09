from datetime import datetime
from re import fullmatch, search
from urllib.parse import ParseResult, quote_plus
from urllib.request import urlopen
from uuid import uuid5, NAMESPACE_URL, UUID

from bs4 import BeautifulSoup, Tag
from weasyprint import CSS, HTML

from . import Scraper
from ..generator import PackageData

class DeviantArt(Scraper):
	domain = 'deviantart.com'

	@staticmethod
	def scrape(url: ParseResult) -> PackageData:
		_STORE_NAME = 'DeviantArt'
		_STORE_PREFIX = 'DVNT'

		request = urlopen(f"https://backend.deviantart.com/oembed?format=xml&url={quote_plus(url.geturl())}")
		soup = BeautifulSoup(request.read(), 'xml')

		if (type := soup.select_one('type')) and type.get_text() == 'link' and (link_url := soup.select_one('url')):
			canonical_url = link_url.get_text()
		else:
			canonical_url = url.geturl()

		sku = int(sku_match.group(1)) if (sku_match := search(r'-(\d+)$', canonical_url)) else None
		name = title.get_text() if (title := soup.select_one('title')) else None
		artists = [author.get_text()] if (author := soup.select_one('author_name')) else []
		pubdate = pubdate.get_text() if (pubdate := soup.select_one('pubdate')) else None
		product_image = image.get_text() if (image := soup.select_one('fullsize_url')) else None

		if product_image:
			soup = BeautifulSoup(urlopen(canonical_url).read(), 'lxml')
		else:
			product_image = image.get_text() if (image := soup.select_one('url')) else None
			soup = BeautifulSoup(urlopen(url.geturl()).read(), 'lxml')

		da_app_url = da_app_element.attrs['content'] if isinstance(da_app_element := soup.find('meta', attrs={'property': 'da:appurl'}), Tag) else None
		global_id = UUID(uuid_match.group(1)) if da_app_url and (uuid_match := fullmatch(r'DeviantArt://deviation/([0-9A-Z]{8}-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{12})', da_app_url)) else uuid5(NAMESPACE_URL, canonical_url)
		description = desc_element if (desc_element := soup.select_one('#description div')) else None

		html = BeautifulSoup('', 'lxml')
		stylesheet = CSS(string='@page { margin: 1em; } img { max-width: 100%; }')

		h1 = soup.new_tag(name='h1')	# pyright: ignore[reportUnknownMemberType]
		h1.string = name or 'Unknown Product Name'
		html.append(h1)

		if artists:
			h2 = soup.new_tag(name='h2')	# pyright: ignore[reportUnknownMemberType]
			h2.string = f"By {artists[0]}"
			html.append(h2)

		if pubdate:
			h3 = soup.new_tag(name='h3')	# pyright: ignore[reportUnknownMemberType]
			h3.string = f"Published {datetime.fromisoformat(pubdate).strftime('%Y-%m-%d')}"
			html.append(h3)

		if description:
			html.append(soup.new_tag('hr'))	# pyright: ignore[reportUnknownMemberType]
			html.append(description)
			description = description.get_text('\n')
		else:
			description = None

		if product_image:
			html.append(soup.new_tag('hr'))	# pyright: ignore[reportUnknownMemberType]
			img = soup.new_tag('img')  # pyright: ignore[reportUnknownMemberType]
			img.attrs['src'] = product_image
			html.append(img)
			product_image = urlopen(product_image)
		else:
			product_image = None

		return PackageData(
			global_id = global_id,
			prefix = _STORE_PREFIX,
			store = _STORE_NAME,
			sku = sku,
			name = name,
			artists = artists,
			description = description,
			image = product_image,
			readme = HTML(string=html.decode_contents()).write_pdf(stylesheets=[stylesheet])
		)

		return PackageData()