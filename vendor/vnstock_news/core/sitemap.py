_D='coerce'
_C=False
_B=None
_A='lastmod'
import requests,urllib3,pandas as pd
from io import StringIO
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Optional
from vnstock_news.config.const import DEFAULT_HEADERS
from vnstock_news.core.base import BaseParser
class Sitemap(BaseParser):
	'\n    Parser for XML sitemaps into a DataFrame of URLs and optional lastmod dates.\n    '
	def __init__(A,url,show_log=_C):'\n        Parameters:\n            url (str): The sitemap URL to download.\n            show_log (bool): Turn debug logging on/off.\n        ';super().__init__(show_log);A.url=url
	def fetch(A):'\n        Download the sitemap XML as text.\n        ';A.logger.info(f"Fetching sitemap from {A.url}");B=requests.get(A.url,headers=DEFAULT_HEADERS,timeout=30,verify=_C);B.raise_for_status();return B.text
	def parse(C,raw):
		"\n        Parse sitemap XML string manually into DataFrame ['url', 'lastmod'].\n        ";B='url';from bs4 import BeautifulSoup as G
		try:
			D=G(raw,'xml');E=D.find_all(B)
			if not E:C.logger.warning('No URLs found with xml parser, falling back to html.parser');import warnings as L;from bs4 import XMLParsedAsHTMLWarning as M;L.filterwarnings('ignore',category=M);D=G(raw,'html.parser');E=D.find_all(B)
			F=[]
			for H in E:
				I=H.find('loc');J=H.find(_A)
				if I:
					K={B:I.text.strip()}
					if J:K[_A]=J.text.strip()
					F.append(K)
			if not F:C.logger.warning('No URLs found in sitemap.')
			A=pd.DataFrame(F)
			if _A in A.columns:A[_A]=pd.to_datetime(A[_A],errors=_D)
			if B in A.columns:
				from urllib.parse import urlparse as N
				def O(u):
					try:A=N(u).path;return bool(A and A!='/'and len(A)>10)
					except:return _C
				A=A[A[B].apply(O)]
			return A[[B,_A]]if _A in A.columns else A[[B]]
		except Exception as P:C.logger.error(f"Failed to parse sitemap manually: {P}");return pd.DataFrame(columns=[B,_A])
	def filter_by_date(C,df,start=_B,end=_B):
		'\n        Filter DataFrame rows by lastmod between `start` and `end`.\n        If no lastmod column, returns df unchanged.\n        ';B=start;A=df
		if _A not in A.columns or A[_A].isnull().all():return A
		A[_A]=pd.to_datetime(A[_A],errors=_D).dt.tz_localize(_B)
		if B:A=A[A[_A]>=pd.Timestamp(B).tz_localize(_B)]
		if end:A=A[A[_A]<=pd.Timestamp(end).tz_localize(_B)]
		return A