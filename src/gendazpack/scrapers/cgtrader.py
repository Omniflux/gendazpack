import json

from urllib.parse import ParseResult, urlparse
from urllib.request import urlopen
from uuid import uuid5, NAMESPACE_URL

from bs4 import BeautifulSoup, Tag
from weasyprint import CSS, HTML

from . import Scraper
from ..generator import PackageData

class RenderHub(Scraper):
	domain = 'cgtrader.com'

	@staticmethod
	def scrape(url: ParseResult, auth: list[str] | None) -> PackageData:
		_STORE_NAME = 'CGTrader'
		_STORE_PREFIX = 'CGTRADR'

		request = urlopen(url.geturl())
		actual_url = urlparse(str(request.url))
		soup = BeautifulSoup(request.read(), 'lxml')

		base_url = base_tag.attrs['href'] if (base_tag := soup.select_one('base[href]')) else f'{ actual_url.scheme }://{ actual_url.netloc }'
		page_type = type_element.attrs['content'] if isinstance(type_element := soup.find('meta', attrs={'property': 'og:type'}), Tag) else None
		canonical_url = url_element.attrs['content'] if isinstance(url_element := soup.find('meta', attrs={'property': 'og:url'}), Tag) else None

		if canonical_url and page_type == 'product':
			global_id = uuid5(NAMESPACE_URL, canonical_url)

			name = " ".join(title_element.attrs['content'].removesuffix(' | 3D model').strip().split()) if isinstance(title_element := soup.find('meta', attrs={'property': 'og:title'}), Tag) else None
			sku = int(info.get_text().lstrip('#')) if (info := soup.select_one('div.details-area__section-info > span:-soup-contains("#")')) else None
			product_image = urlopen(img_element.attrs['content']) if isinstance(img_element := soup.find('meta', attrs={'property': 'og:image'}), Tag) and img_element.attrs['content'] else None
			artists = [artist.get_text()] if (artist := soup.select_one('a.seller-area__header-content-username')) else []

			pubdate = info.get_text() if (info := soup.select_one('span.details-area__section-subtitle:-soup-contains("Publish date") + div.details-area__section-info > span')) else None
			description = soup.select_one('div.description-area__body-content')
			product_image_data = json.loads(data.attrs['data-react-props'])['galleryArea']['medias'] if isinstance(data := soup.find('div', attrs={'data-react-class': 'ItemPage/TopSection/TopSection'}), Tag) else None

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
				if (div := description.select_one('div:first-child')) and div.get_text() == 'Description':
					div.decompose()

				if div := description.select_one('div.tags-list'):
					div.decompose()

				html.append(soup.new_tag('hr'))	# pyright: ignore[reportUnknownMemberType]
				html.append(description)
				description = description.get_text('\n')
			else:
				description = None

			if product_image_data:
				for media in product_image_data:
					img = soup.new_tag('img')  # pyright: ignore[reportUnknownMemberType]
					img.attrs['src'] = media['imageName']
					html.append(img)

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
