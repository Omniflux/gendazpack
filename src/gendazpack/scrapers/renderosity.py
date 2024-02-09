from re import search
from typing import cast
from urllib.parse import ParseResult, quote_plus, urlparse
from urllib.request import urlopen
from uuid import uuid5, NAMESPACE_URL

from bs4 import BeautifulSoup, Tag
from weasyprint import CSS, HTML

from . import Scraper
from ..generator import PackageData

class Renderosity(Scraper):
	domain = 'renderosity.com'

	@staticmethod
	def scrape(url: ParseResult) -> PackageData:
		_STORE_NAME = 'Renderosity'
		_STORE_PREFIX = 'ROSITY'

		_FREE_NAME = 'Renderosity Free'
		_FREE_PREFIX = 'ROSITYF'

		request = urlopen(url.geturl())
		actual_url = urlparse(str(request.url))
		soup = BeautifulSoup(request.read(), 'lxml')

		base_url = base_tag.attrs['href'] if (base_tag := soup.select_one('base[href]')) else f'{ actual_url.scheme }://{ actual_url.netloc }'
		page_type = type_element.attrs['content'] if isinstance(type_element := soup.find('meta', attrs={'property': 'og:type'}), Tag) else None
		canonical_url = url_element.attrs['content'] if isinstance(url_element := soup.find('meta', attrs={'property': 'og:url'}), Tag) else None

		if canonical_url and page_type in ('item', 'product'):
			html = BeautifulSoup('', 'lxml')
			stylesheet = CSS(string='@page { margin: 1em; } img { max-width: 100%; } @page my_page { size: landscape; } .rr-mkt-product-image { page: my_page; }')
			global_id = uuid5(NAMESPACE_URL, canonical_url)
			description = description_element.attrs['content'] if isinstance(description_element := soup.find('meta', attrs={'property': 'og:description'}), Tag) else None
			product_image = urlopen(img_element.attrs['content']) if isinstance(img_element := soup.find('meta', attrs={'property': 'og:image'}), Tag) and img_element.attrs['content'] else None

			if url.path.lower().startswith('/freestuff/'):
				if soup.find('meta', attrs={'property': 'og:type', 'content': 'item'}):

					sku = int(sku_match.group(0)) if (sku_match := search(r'(\d+)', canonical_url)) else None
					name = title_element.attrs['content'] if isinstance(title_element := soup.find('meta', attrs={'property': 'og:title'}), Tag) else None
					artists = [a.get_text() for a in soup.select('.rr-fsitem-byline > a')]

					if product_html := soup.select_one('div.rr-fsitem'):
						if downloads := product_html.select_one('span.rr-fsitem-downloads'):
							downloads.replace_with(soup.new_tag('hr'))  # pyright: ignore[reportUnknownMemberType]
						if section := product_html.select_one('span.rr-fsitem-section'):
							for a in section.findAll('a'):
								a.replaceWithChildren()
						html.append(product_html)

					if not product_image and name:
						search_request = urlopen(f'https://www.renderosity.com/users/{quote_plus(artists[0])}/freestuff?keyword={quote_plus(name)}')
						search_soup = BeautifulSoup(search_request.read(), 'lxml')
						product_image = urlopen(img_element.attrs['src']) if (img_element := search_soup.select_one(f'div[data-id="{sku}"] img.rr-fsitem-tile-thumbnail')) and img_element.attrs['src'] else None

					return PackageData(
						global_id = global_id,
						prefix = _FREE_PREFIX,
						store = _FREE_NAME,
						sku = sku,
						name = name,
						artists = artists,
						description = description,
						image = product_image,
						readme = HTML(string=html.decode_contents(), base_url=base_url).write_pdf(stylesheets=[stylesheet])
					)
			else:
				if soup.find('meta', attrs={'property': 'og:type', 'content': 'product'}):

					sku = int(sku_element.attrs['data-id']) if (sku_element := soup.select_one('div.rr-mkt-product-container')) else None
					name = name_element.get_text() if (name_element := soup.select_one('span.rr-mktproduct-title')) else None
					artists = [a.get_text() for a in soup.select('.rr-mktproduct-byline > a')]

					if product_html := soup.select_one('div.rr-item-view'):
						if img := product_html.select_one('div.rr-mkt-product-imageline'):
							img.replace_with(soup.new_tag('hr'))  # pyright: ignore[reportUnknownMemberType]
						if video := product_html.select_one('div.rr-mkt-product-360-video-wrapper'):
							video.decompose()
						for cover in product_html.select('div.rr-nudity-cover'):
							cover.decompose()
						for sidebar in product_html.select('div.rr-mktproduct-sidebar'):
							sidebar.decompose()
						if departments := product_html.select_one('div.rr-mkt-product-departments'):
							departments.decompose()

						if info_wrapper := product_html.select_one('div.rr-mkt-product-additional_info-wrapper'):
							for element in info_wrapper.find_next_siblings():
								cast(Tag, element).decompose()
							info_wrapper.extract()
							if (info_url := info_url.attrs['data-additional_info_url'] if (info_url := info_wrapper.select_one('ul.nav')) else None):
								for pane in info_wrapper.select('a.nav-link'):
									if (href := pane['href']) in ('#description', '#editorial'):
										pane_content = BeautifulSoup(urlopen(f'{ info_url }?pane={ href.lstrip('#') }').read(), 'lxml')
#										if href == '#editorial':
#											x = pane_content.select_one('body > table table:nth-child(12)').decompose()

										if pane_content and (pane_content.find('img') or pane_content.get_text(strip=True) != ''):
											product_html.append(soup.new_tag('hr'))  # pyright: ignore[reportUnknownMemberType]
											header = soup.new_tag('h1')  # pyright: ignore[reportUnknownMemberType]
											header.append(pane.decode_contents())
											product_html.append(header)
											product_html.append(pane_content)

						html.append(product_html)

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