_C='html.parser'
_B='tag'
_A=True
import requests,urllib3
from bs4 import BeautifulSoup
import html2text
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Dict,Any,Optional
from vnstock_news.config.const import DEFAULT_HEADERS
from vnstock_news.utils.logger import setup_logger
from vnstock_news.core.base import BaseParser
class News(BaseParser):
	'\n    Parser for extracting metadata and content from a single news article.\n    '
	def __init__(A,url,config,show_log=False):'\n        Parameters:\n            url (str): Optional sitemap URL placeholder (ignored).\n            config (dict): CSS selectors for title/content/etc.\n            show_log (bool): Turn debug logging on/off.\n        ';super().__init__(show_log);A.config=config
	def fetch(A):'\n        Download the HTML of one article.\n        ';raise NotImplementedError('Use fetch_article(url) instead')
	def fetch_article(B,url):'\n        Fetch and return raw HTML for a given article URL.\n        ';B.logger.info(f"Fetching article HTML: {url}");A=requests.get(url,headers=DEFAULT_HEADERS,timeout=60,verify=False);A.raise_for_status();return A.text
	def parse(A,raw_html):
		'\n        Extract metadata fields from HTML string.\n        ';F='content';E='strong';D='meta';import re;B=BeautifulSoup(raw_html,_C)
		def C(sel):
			A=sel
			if not A:return
			D=A.get(_B);E={A:B for(A,B)in A.items()if A!=_B};C=B.find(D,attrs=E);return C.get_text(strip=_A)if C else None
		def G(sel):
			C=sel
			if not C:return
			G=C.get(_B);H={A:B for(A,B)in C.items()if A!=_B};D=B.find(G,attrs=H)
			if D:
				F=D.find_all(['a','span',E])
				if F:
					A=[A.get_text(strip=_A)for A in F if A.get_text(strip=_A)]
					if A:A=[A for A in A if not re.match('^tag|^chủ đề',A,re.I)];return', '.join(A)
				return D.get_text(strip=_A)
		def H(sel):
			A=C(sel)
			if A:
				B=re.search('([\\d\\.,]+)',A)
				if B:
					D=B.group(1).replace(',','').replace('.','')
					if D.isdigit():return int(D)
		def I():
			D=C(A.config.get('author_selector'))
			if D:return D
			for F in B.find_all('p',align='right'):
				G=F.find(E)or F.find('b')
				if G:return G.get_text(strip=_A)
		def J():A=B.find(D,property='og:image')or B.find(D,attrs={'name':'twitter:image'});return A.get(F)if A else None
		def K():
			C=B.find(D,property='article:section')
			if C:return C.get(F)
			for A in B.find_all('script'):
				if A.string and'ArticleCategory'in A.string:
					E=re.search('[\'\\"]ArticleCategory[\'\\"]\\s*:\\s*[\'\\"]([^\'\\"]+)[\'\\"]',A.string)
					if E:return E.group(1)
		return{'title':C(A.config.get('title_selector')),'short_description':C(A.config.get('short_desc_selector')),'publish_time':C(A.config.get('publish_time_selector')),'author':I(),'image_url':J(),'category':K()or C(A.config.get('category_selector')),'tags':G(A.config.get('tags_selector')),'view_counts':H(A.config.get('view_counts_selector'))}
	def to_markdown(D,raw_html,retain_links=_A,retain_images=_A):
		'\n        Convert main article content into Markdown.\n        ';E=BeautifulSoup(raw_html,_C);A=D.config.get('content_selector')
		if not A:raise ValueError("Missing 'content_selector'")
		F=A.get(_B);G={A:B for(A,B)in A.items()if A!=_B};C=E.find(F,attrs=G)
		if not C:raise ValueError('Article content not found')
		B=html2text.HTML2Text();B.ignore_links=not retain_links;B.ignore_images=not retain_images;return B.handle(str(C))