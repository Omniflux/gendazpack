from re import search, IGNORECASE
from urllib.parse import ParseResult, urljoin, urlparse, parse_qs
from urllib.request import urlopen, Request
from uuid import uuid5, NAMESPACE_URL

from bs4 import BeautifulSoup, Tag
from weasyprint import CSS, HTML

from . import Scraper
from ..generator import PackageData

class Renderotica(Scraper):
	domain = 'renderotica.com'

	@staticmethod
	def scrape(url: ParseResult) -> PackageData:
		_STORE_NAME = 'Renderotica'
		_STORE_PREFIX = 'ROTICA'

		request = urlopen(Request(url.geturl(), headers={'User-Agent': 'Mozilla'}))
		actual_url = urlparse(str(request.url))
		soup = BeautifulSoup(request.read(), 'lxml')

		base_url = base_tag.attrs['href'] if (base_tag := soup.select_one('base[href]')) else f'{ actual_url.scheme }://{ actual_url.netloc }'

		if actual_url.hostname == 'web.archive.org' and (suburl := search('(https?://.*)', url.path, IGNORECASE)):
			canonical_url = urlparse(suburl.group(0)).geturl().split('_', 1)[0] + '_'
		else:
			canonical_url = actual_url.geturl().split('_', 1)[0] + '_'

		global_id = uuid5(NAMESPACE_URL, canonical_url)
		sku = int(sku_match.group(1)) if (sku_match := search(r'/sku/(\d+)', canonical_url)) else None

		
		if (product_listing := soup.select_one('#product-listing')) and (product_info := product_listing.select_one('div.product-info')):
			product_content = soup.select_one('div.product-listing-content')
			product_content_old = soup.select_one('#product-info-panes')

			if product_content or product_content_old:
				html = BeautifulSoup('', 'lxml')
				stylesheet = CSS(string='''
					@page { margin: 1em; }
					img { max-width: 100%; }
					.ProductCompatibility td.level2,
					.ProductCompatibility td.level3,
					.ProductCompatibility td.level4
						{ background-color: transparent; }
				''')
				name = name_element.get_text() if (name_element := product_info.select_one('.product-name')) else None
				description = description_element.get_text() if (description_element := product_info.select_one('.summary')) else None
				product_image = urljoin(base_url, img_element.attrs['src']) if (img_element := product_listing.select_one('.primary-image img[src]')) else None
				artists = [vendor_element.get_text() for vendor_element in  product_info.select('a.vendor')]

				if pinterest := product_info.select_one('#p_lt_zoneContent_pageplaceholder_p_lt_zoneContentBody_CGBytes_ProductDetail_ctl01_hlkPinterest[href]'):
					product_image = parse_qs(urlparse(pinterest.attrs['href']).query)['media'][0]

				if description_element and (sku_element := product_info.select_one('#p_lt_zoneContent_pageplaceholder_p_lt_zoneContentBody_CGBytes_ProductDetail_lblSkuNumber[title]')):
					released_date = soup.new_tag('div')	# pyright: ignore[reportUnknownMemberType]
					released_date.string = sku_element.attrs['title']
					description_element.insert_before(released_date)

				if price := product_info.select_one('.price'):
					for sibling in price.find_next_siblings():
						if isinstance(sibling, Tag) and not ((bundle := sibling.find(class_='bundle')) and bundle and bundle.get_text().startswith('Products in this bundle:')):
							sibling.decompose()
					price.decompose()

				html.append(product_info)

				images = product_listing.select_one('div.image-navigation') or soup.new_tag('div')	# pyright: ignore[reportUnknownMemberType]
				for a in images.find_all('a'):
					a.replace_with(soup.new_tag('img', attrs={'src': a.attrs['href'], 'title': a.attrs['title'], 'alt': a.attrs['title']}))  # pyright: ignore[reportUnknownMemberType]

				if product_content:
					panes = product_content.select('.product-panes > .pane > h1')
					for pane in panes:
						if pane.get_text() in ('Downloads', 'Accessories', 'Related Products'):
							if isinstance(parent := pane.parent, Tag):
								if isinstance(next_sibling := parent.find_next_sibling(), Tag) and next_sibling.name == 'hr':
									next_sibling.decompose()
								parent.decompose()

					html.append(product_content)

				elif product_content_old:
					img = soup.new_tag('img', attrs={'src': product_image})  # pyright: ignore[reportUnknownMemberType]
					if img.attrs['src'] not in (i.attrs['href'] for i in images.find_all('a')):
						html.append(img)
					html.append(images)

					for pane_title in ('downloads', 'related-products', 'accessories', 'others-also-purchased'):
						if pane := product_content_old.select_one(f'.pane.{pane_title}'):
							pane.decompose()

					html.append(product_content_old)

				product_image = urlopen(Request(product_image, headers={'User-Agent': 'Mozilla'})) if product_image else None

				return PackageData(
					global_id = global_id,
					prefix = _STORE_PREFIX,
					store = _STORE_NAME,
					sku = sku,
					name = name,
					artists = artists,
					description = description,
					image = product_image,
					readme = HTML(string=html.decode_contents(), base_url=base_url).write_pdf(stylesheets=[stylesheet])#, presentational_hints=True)
				)

		return PackageData()