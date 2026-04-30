'\nAI Agent Diagnostic & Probing Utils.\nThese tools are designed to be used by an AI Agent or developer to automatically diagnose\nand figure out the correct configuration for a new unsupported news site.\n'
_L='sub_sitemaps'
_K='tag'
_J='urlset'
_I='sitemapindex'
_H='rss'
_G='suggestions'
_F=False
_E='div'
_D='id'
_C='type'
_B='urls_found'
_A='class'
import sys,re,json,urllib3,requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HEADERS={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
def probe_sitemap(url):
	'\n    Given a URL, determines if it is a Sitemap Index, a direct URLSet, or RSS Feed.\n    Returns a dictionary characterizing the feed type and discovered URLs.\n    ';H='loc';G='link'
	try:
		C=requests.get(url,headers=HEADERS,timeout=15,verify=_F);C.raise_for_status();A=BeautifulSoup(C.content,'xml')
		if A.find(_H)or A.find('channel'):I=A.find_all('item')[:5];D=[A.find(G).text for A in I if A.find(G)];return{_C:_H,_B:D}
		if A.find(_I):
			F=[A.text for A in A.find_all(H)];E=[]
			for B in F:
				if'year'in B.lower()or'202'in B:E.append((B,'Likely year-based index'))
				if'news'in B.lower()or'post'in B.lower()or'category'in B.lower():E.append((B,'Likely post/category index'))
			return{_C:_I,_L:F,_G:E}
		if A.find(_J):D=[A.text for A in A.find_all(H)][:5];return{_C:_J,_B:D}
		return{_C:'unknown','raw_sample':C.text[:200]}
	except Exception as J:return{'error':str(J)}
def _guess_content_selector(soup):
	'Heuristic to find the main content block that has the most paragraphs.';H=soup.find_all(_E)+soup.find_all('article');A=None;D=0
	for B in H:
		C=B.find_all('p',recursive=_F)
		if not C:C=B.find_all('p')
		E=sum(len(A.text)for A in C)
		if B.name=='body':continue
		if E>D:D=E;A=B
	if A:
		F=A.get(_A);G=A.get(_D)
		if F:return{_A:F[0]}
		elif G:return{_D:G}
		return{_K:A.name}
def probe_article_selectors(url):
	'\n    Fetches an article URL and guesses CSS selectors for title, content, sapo, time, author.\n    ';R='view_counts_selector';Q='view';P='right';O='author_selector';N='span';M='title_selector'
	try:
		E=requests.get(url,headers=HEADERS,timeout=15,verify=_F);E.raise_for_status();B=BeautifulSoup(E.content,'html.parser');A={};D=B.find('h1')
		if D and D.get(_A):A[M]={_A:D.get(_A)[0]}
		else:
			S=B.find('meta',property='og:title')
			if S:A[M]={_K:'h1'}
		F=_guess_content_selector(B)
		if F:A['content_selector']=F
		G=B.find_all(['time',N,_E],class_=re.compile('time|date|publish',re.I))
		if G:A['publish_time_selector']={_A:G[0].get(_A)[0]}
		H=B.find_all(['h2',_E,'p'],class_=re.compile('sapo|summary|desc',re.I))
		if H:A['short_desc_selector']={_A:H[0].get(_A)[0]}
		I=B.find_all([N,_E,'p','a'],class_=re.compile('author|tac-gia',re.I))
		if I:A[O]={_A:I[0].get(_A)[0]}
		else:
			for J in B.find_all('p',align=P):
				T=J.find('strong')or J.find('b')
				if T:A[O]={_K:'p','align':P};break
		K=B.find_all([_E,'ul'],class_=re.compile('tag|keyword',re.I))
		if K:A['tags_selector']={_A:K[0].get(_A)[0]}
		L=B.find_all(attrs={_D:re.compile(Q,re.I)})or B.find_all(class_=re.compile(Q,re.I))
		if L:
			for C in L:
				if'lượt xem'in C.text.lower()or'views'in C.text.lower():
					if C.get(_D):A[R]={_D:C.get(_D)};break
					elif C.get(_A):A[R]={_A:C.get(_A)[0]};break
		return A
	except Exception as U:return{'error':str(U)}
def agent_probe_site(site_url):
	'\n    Full automated diagnosis of a site. Prints recommended JSON block.\n    ';D=site_url;print(f"[*] Starting site probe for: {D}");E=urlparse(D);G=f"{E.scheme}://{E.netloc}";C=urljoin(G,'/sitemap.xml');print(f"[*] Testing default sitemap: {C}");A=probe_sitemap(C);B=None
	if A.get(_C)==_I:
		print('[!] Found Sitemap Index. Sub-sitemaps:')
		for H in A.get(_L,[])[:3]:print(f"  - {H}")
		print('[!] Suggestions:')
		for(I,J)in A.get(_G,[]):print(f"  - {I} ({J})")
		if A.get(_G):
			F=probe_sitemap(A[_G][0][0])
			if F.get(_B):B=F[_B][0]
	elif A.get(_C)in[_J,_H]:print(f"[!] Found direct sitemap/feed containing {len(A.get(_B,[]))} urls.");B=A[_B][0]if A.get(_B)else None
	if not B:print('[!] Could not automatically find an article URL. Please provide one manually to probe_article_selectors.');return
	print(f"\n[*] Extracted sample article: {B}\n[*] Probing article selectors...");K=probe_article_selectors(B);L={'sitemap_url':C,'config':K};print('\n[✔] Recommended site config dictionary:');print(json.dumps(L,indent=4,ensure_ascii=_F))
if __name__=='__main__':
	if len(sys.argv)>1:agent_probe_site(sys.argv[1])
	else:print('Usage: python -m vnstock_news.utils.diagnostics <SITE_URL>')