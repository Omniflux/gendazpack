from html import unescape
from re import search
from urllib.parse import ParseResult, urlsplit
from urllib.request import urlopen, Request
from uuid import uuid5, NAMESPACE_URL

import json

from bs4 import BeautifulSoup, Tag
from weasyprint import CSS, HTML

from . import Scraper
from ..generator import PackageData

class Patreon(Scraper):
	domain = 'patreon.com'

	@staticmethod
	def scrape(url: ParseResult) -> PackageData:
		_STORE_NAME = 'Patreon'
		_STORE_PREFIX = 'PTRN'

		request = urlopen(Request(url.geturl(), headers={'User-Agent': 'Patreon/7.6.28 (Android; Android 11; Scale/2.10)'}))
		actual_url = urlsplit(str(request.url))
		soup = BeautifulSoup(request.read(), 'lxml')

		if head := soup.select_one('head'):
			base_url = base_tag.attrs['href'] if (base_tag := head.select_one('base[href]')) else f'{ actual_url.scheme }://{ actual_url.netloc }'
			canonical_url = url_element.attrs['content'] if isinstance(url_element := head.find('meta', attrs={'property': 'og:url'}), Tag) else None

			if canonical_url:
				sku = int(post_id.group(0)) if (post_id := search(r'\d+$', canonical_url)) else None
				global_id = uuid5(NAMESPACE_URL, f'https://www.patreon.com/posts/{sku}')

				ldjson = json.loads(unescape(head.select_one('script[type="application/ld+json"]').string))	# pyright: ignore[reportArgumentType, reportUnknownArgumentType, reportOptionalMemberAccess]
				name = ldjson['name']
				description = ldjson['description']
				artists = [ ldjson['author']['name'] ]

				data = json.loads(script.string) if isinstance(script := soup.find(id='__NEXT_DATA__', attrs={'type': 'application/json'}), Tag) else None	# pyright: ignore[reportArgumentType]
				if data:
					product_image = data['props']['pageProps']['bootstrapEnvelope']['pageBootstrap']['post']['data']['attributes']['image']['url']

					if post_card := soup.select_one('div[data-tag=post-card]'):
						for x in post_card.select('div[data-tag=chip-container]'):
							x.parent.decompose()	# pyright: ignore[reportOptionalMemberAccess]

						for x in post_card.select('div[data-tag=post-attachments]'):
							x.decompose()

						for x in post_card.select('a[data-tag=post-tag]'):
							x.unwrap()

						if post_details := post_card.select_one('div[data-tag=post-details]'):
							for x in post_details.next_elements:
								x.decompose() if isinstance(x, Tag) else x.extract()
							post_details.decompose()

						if x := post_card.select_one('svg[aria-label=Loading]'):
							x.decompose()

						html = BeautifulSoup('', 'lxml')
						stylesheet = CSS(string='@page { margin: 1em; } img { max-width: 100%; } svg { width: 16px; }')

						html.append(post_card)
					else:
						html = stylesheet = None

					return PackageData(
						global_id = global_id,
						prefix = _STORE_PREFIX,
						store = _STORE_NAME,
						sku = sku,
						name = name,
						artists = artists,
						description = description,
						image = urlopen(Request(product_image, headers={'User-Agent': 'Patreon/7.6.28 (Android; Android 11; Scale/2.10)'})),
						readme = HTML(string=html.decode_contents(), base_url=base_url).write_pdf(stylesheets=[stylesheet]) if html else None
					)

		return PackageData()