import json

from re import search
from typing import cast
from urllib.parse import ParseResult, urlparse
from urllib.request import urlopen
from uuid import uuid5, NAMESPACE_URL

from bs4 import BeautifulSoup, Tag
from weasyprint import CSS, HTML

from . import Scraper
from ..generator import PackageData

class RenderHub(Scraper):
	domain = 'renderhub.com'

	@staticmethod
	def scrape(url: ParseResult) -> PackageData:
		_STORE_NAME = 'RenderHub'
		_STORE_PREFIX = 'RNDRHUB'

		request = urlopen(url.geturl())
		actual_url = urlparse(str(request.url))
		soup = BeautifulSoup(request.read(), 'lxml')

		base_url = base_tag.attrs['href'] if (base_tag := soup.select_one('base[href]')) else f'{ actual_url.scheme }://{ actual_url.netloc }'
		canonical_url = url_element.attrs['content'] if isinstance(url_element := soup.find('meta', attrs={'property': 'og:url'}), Tag) else None

		if canonical_url:
			global_id = uuid5(NAMESPACE_URL, canonical_url)

			ratings_script = ratings_script.get_text() if (ratings_script := soup.select_one('div.itemInfo script:-soup-contains("function showRat(p)")')) else None
			sku = int(sku_match.group(1)) if ratings_script and (sku_match := search(r'"i=(\d+)&p="', ratings_script)) else None

			pubDate_tag = pubLabel.parent.next_sibling if (pubLabel := soup.select_one('div.itemInfo table.infoTable b:-soup-contains("Published:")')) else None	# pyright: ignore[reportOptionalMemberAccess]
			pubdate = pubDate_tag.get_text() if pubDate_tag else None

			name = img.attrs['title'] if (img := soup.select_one('#mainImg')) else None
			description = soup.select_one('div.prodInfo')

			ldjson: list[dict[str, str]] | None = json.loads(ldjson_str.text) if (ldjson_str := soup.select_one('script[type="application/ld+json"]')) else None
			if ldjson and (data := next(filter(lambda x: isinstance(x, dict) and x.get('@type') == 'Product', ldjson), None)):	# pyright: ignore[reportUnnecessaryIsInstance]
				if not name:
					name = data.get('name', None)

				artists = [artist] if (artist := cast(dict[str, dict[str, str]], data).get('brand', {}).get('name', None)) else []
				images = cast(dict[str, list[str]], data).get('image', [])

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
					h3.string = f"Published {pubdate}"
					html.append(h3)

				if description:
					html.append(soup.new_tag('hr'))	# pyright: ignore[reportUnknownMemberType]
					html.append(description)
					description = description.get_text('\n')
				else:
					description = None

				if images:
					product_image = urlopen(images[0])
					html.append(soup.new_tag('hr'))	# pyright: ignore[reportUnknownMemberType]
					for image in images:
						img = soup.new_tag('img')  # pyright: ignore[reportUnknownMemberType]
						img.attrs['src'] = image
						html.append(img)
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
					readme = HTML(string=html.decode_contents(), base_url=base_url).write_pdf(stylesheets=[stylesheet])
				)

		return PackageData()