import zlib
import warnings

from re import findall, search
from ssl import SSLContext
from urllib.parse import ParseResult, urljoin, urlparse
from urllib.request import urlopen, Request
from uuid import uuid5, NAMESPACE_URL

from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning
from weasyprint import CSS, HTML
from weasyprint.urls import StreamingGzipFile

from . import Scraper
from ..generator import PackageData

class ShareCG(Scraper):
	domain = 'sharecg.com'

	# ShareCG requires known User-Agent, does not recognize WeasyPrint, so override
	@staticmethod
	def mozilla_url_fetcher(url: str, timeout: int = 10, ssl_context: SSLContext | None = None):
		HTTP_HEADERS = {
			'User-Agent': 'Mozilla',
			'Accept': '*/*',
			'Accept-Encoding': 'gzip, deflate',
		}

		response = urlopen(Request(url, headers=HTTP_HEADERS), timeout=timeout, context=ssl_context)
		response_info = response.info()
		result = {
			'redirected_url': response.geturl(),
			'mime_type': response_info.get_content_type(),
			'encoding': response_info.get_param('charset'),
			'filename': response_info.get_filename(),
		}
		content_encoding = response_info.get('Content-Encoding')
		if content_encoding == 'gzip':
			result['file_obj'] = StreamingGzipFile(fileobj=response)
		elif content_encoding == 'deflate':
			data = response.read()
			try:
				result['string'] = zlib.decompress(data)
			except zlib.error:
				# Try without zlib header or checksum
				result['string'] = zlib.decompress(data, -15)
		else:
			result['file_obj'] = response
		return result

	@staticmethod
	def scrape(url: ParseResult) -> PackageData:
		_STORE_NAME = 'ShareCG'
		_STORE_PREFIX = 'SHARECG'

		request = urlopen(Request(url.geturl(), headers={'User-Agent': 'Mozilla'}))
		actual_url = urlparse(str(request.url))

		# ShareCG serves broken XHTML, so xml parser does not work. Use lxml (HTML) parser instead and suppress warning
		with warnings.catch_warnings():
			warnings.simplefilter('ignore', XMLParsedAsHTMLWarning)
			soup = BeautifulSoup(request.read(), 'lxml')

		base_url = base_tag.attrs['href'] if (base_tag := soup.select_one('base[href]')) else f'{ actual_url.scheme }://{ actual_url.netloc }'
		canonical_url = url_element.attrs['content'].partition('browse/')[0] if isinstance(url_element := soup.find('meta', attrs={'name': 'twitter:url'}), Tag) else None

		if canonical_url:
			html = BeautifulSoup('', 'lxml')
			stylesheet = CSS(string='@page { margin: 1em; } img { max-width: 100%; }')

			global_id = uuid5(NAMESPACE_URL, canonical_url)
			sku = int(sku_match.group(1)) if (sku_match := search(r'(\d+)', canonical_url)) else None

			if content_html := soup.select_one('#topHalf'):
				name_element = content_html.select_one('div.ViewUploadTitle')
				product_image_url = findall(r'\d+', string=a_element.attrs['onclick'])[0] if (a_element := content_html.select_one("a.dialog_link_view_WebPage_img")) and 'onclick' in a_element.attrs else None
				if not product_image_url:
					product_image_url = img.attrs['src'] if (img := content_html.select_one("#imagefocus img")) and img.attrs['src'] else None

				if desc_element := content_html.select_one('#moreUploadInfo'):
					del desc_element.attrs['style']
					if a := desc_element.select_one('a:last-child'):
						a.decompose()
				else:
					desc_element = content_html.select_one('#moreUploadInfoExpander')

				name = name_element.get_text() if name_element else None
				description = desc_element.get_text() if desc_element else None
				artists = [artist_element.get_text().rpartition(' ')[0]] if (artist_element := content_html.select_one('a.headerLink')) else []

				if name_element:
					html.append(name_element)

				if artists:
					by = soup.new_tag('div')  # pyright: ignore[reportUnknownMemberType]
					by.string = f'By: {artists[0]}'
					html.append(by)

				html.append(soup.new_tag('hr'))	# pyright: ignore[reportUnknownMemberType]

				if desc_element:
					html.append(desc_element)

				html.append(soup.new_tag('hr'))	# pyright: ignore[reportUnknownMemberType]

				if metadata := content_html.select_one('span.uploadInfoLists'):
					html.append(metadata)

				if product_image_url:
					img = soup.new_tag('img')  # pyright: ignore[reportUnknownMemberType]
					img.attrs['src'] = f'/get_image.php?upload_image_id={ product_image_url }' if product_image_url.isdigit() else product_image_url
					html.append(img)
					product_image = urlopen(Request(urljoin(base_url, img.attrs['src']), headers={'User-Agent': 'Mozilla'}))

					if images := content_html.select('div.imageChooser a'):
						for id in [findall(r'\d+', x.attrs['onclick'])[0] for x in images]:
							if id != product_image_url:
								img = soup.new_tag('img')  # pyright: ignore[reportUnknownMemberType]
								img.attrs['src'] = f'/get_image.php?upload_image_id={ id }'
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
					readme = HTML(string=html.decode_contents(), base_url=base_url, url_fetcher=ShareCG.mozilla_url_fetcher).write_pdf(stylesheets=[stylesheet])
				)

		return PackageData()