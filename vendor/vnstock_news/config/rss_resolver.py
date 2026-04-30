import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
from typing import Dict,List,Optional
from vnstock_news.config.const import DEFAULT_HEADERS
from vnstock_news.utils.logger import setup_logger
from datetime import datetime
class DynamicRssResolver:
	'\n    Dynamically resolves RSS URLs from an HTML Index page.\n    '
	def __init__(A,debug=False):A.logger=setup_logger(A.__class__.__name__,debug);A.cache={}
	def get_rss_urls(A,site_name,base_config):
		'\n        Takes an index_url and returns a list of absolute RSS URLs.\n        ';C=site_name;I=base_config.get('rss',{});J=I.get('urls',[])
		if J:return J
		B=I.get('index_url')
		if not B:return[]
		F=f"{C}_rss_{B}"
		if F in A.cache:
			L,M=A.cache[F]
			if(datetime.now()-L).total_seconds()<3600:A.logger.debug(f"Using cached RSS URLs for {C}");return M
		try:
			A.logger.info(f"Probing {C} RSS Index: {B}");K=requests.get(B,headers=DEFAULT_HEADERS,timeout=15,verify=False);K.raise_for_status();N=BeautifulSoup(K.content,'html.parser');G=urlparse(B);O=f"{G.scheme}://{G.netloc}";D=[]
			for P in N.find_all('a',href=True):
				E=P['href']
				if'.rss'in E.lower()or'/rss/'in E.lower()or'rss.xml'in E.lower():
					H=urljoin(O,E)
					if urlparse(H).netloc==G.netloc:
						if H not in D:D.append(H)
			if D:A.cache[F]=datetime.now(),D;return D
			A.logger.warning(f"No RSS links found dynamically on {B} for {C}");return[]
		except Exception as Q:A.logger.error(f"Error extracting dynamic RSS for {C} at {B}: {Q}");return[]