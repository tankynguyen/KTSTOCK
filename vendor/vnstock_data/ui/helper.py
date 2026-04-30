'\nHelper utilities for vnstock_data Unified UI.\nProvides tools to easily explore API structure and documentation.\n'
_V='Series'
_U='DataFrame'
_T='derivatives'
_S='__name__'
_R='VIC'
_Q='GC=F'
_P='commodity'
_O='USDVND'
_N='forex'
_M='BTC'
_L='crypto'
_K='symbol'
_J='self'
_I='Market'
_H='Reference'
_G='return'
_F='Macro'
_E=None
_D='VNINDEX'
_C='index'
_B=True
_A=False
import inspect,pandas as pd
from typing import Any,Optional,Set
_DEPRECATED_METHODS={'pe','pb','evaluation','gdp','cpi','industry_prod','import_export','retail','fdi','money_supply','population_labor','exchange_rate','interest_rate',_T}
_BACKWARD_COMPAT_ALIASES={'price_board','history','intraday','price_depth','trading_stats','put_through','matched_by_price','by_group','by_exchange'}
_MARKET_TOPLEVEL_ENDPOINTS_HIDE={'quote'}
def _is_endpoint_method(method):
	'\n    Check if a method is an endpoint (returns data/DataFrame, not a domain object).\n    Endpoints are actual data-returning methods that dispatch to providers,\n    not relay methods that call other layer methods.\n    ';C=method
	try:
		E=getattr(C,'__annotations__',{});D=E.get(_G)
		if D:
			B=str(D)
			if _U in B or _V in B or'dict'in B or'list'in B:
				try:
					A=inspect.getsource(C)
					if'Analytics()'in A or'Macro()'in A or'Reference()'in A:return _A
					return _B
				except(OSError,TypeError):return _B
		try:
			A=inspect.getsource(C)
			if'_dispatch'in A:return _B
		except(OSError,TypeError):pass
		return _A
	except(OSError,TypeError):return _A
def _should_include_method(name,method,is_macro_layer=_A,parent_name=''):
	"Determine if a method should be displayed in the API tree.\n    \n    Args:\n        name: Method name\n        method: Method object\n        is_macro_layer: True if this is the Macro layer\n        parent_name: Parent class/layer name (e.g., 'Market' at top level)\n    ";C=parent_name;B=method;A=name
	if A.startswith('_'):return _A
	if not callable(B)and not isinstance(B,property):return _A
	if A in _BACKWARD_COMPAT_ALIASES:return _A
	if A in _DEPRECATED_METHODS:
		if is_macro_layer or A==_T and C==_H:return _A
	if C==_I and A in _MARKET_TOPLEVEL_ENDPOINTS_HIDE:return _A
	return _B
def _get_public_methods(obj,include_intermediate=_A,parent_name=''):
	"\n    Helper to extract public callable methods from an object, excluding dunders and unwanted methods.\n    \n    Args:\n        obj: Object to extract methods from\n        include_intermediate: If True, include navigation methods (returns domain objects).\n                            If False, only include endpoint methods (returns data).\n        parent_name: Parent class name for context-aware filtering (e.g., 'Market')\n    ";B=[];D=type(obj).__name__;E=D==_F
	for(C,A)in inspect.getmembers(obj,predicate=inspect.ismethod):
		if not _should_include_method(C,A,E,parent_name):continue
		if not include_intermediate:
			if not _is_endpoint_method(A):continue
		B.append((C,A))
	return B
def show_doc(obj):
	"\n    Prints the complete docstring and signature of a function or class.\n    \n    Args:\n        obj: Function, method, class or its name as string (e.g., 'Market', 'Reference').\n             When using strings, the object will be automatically resolved from vnstock_data UI.\n    ";B=obj
	if isinstance(B,str):
		try:
			from vnstock_data import ui;L=B.replace('()','').strip();G=L.split('.')
			if hasattr(ui,G[0]):
				H=getattr(ui,G[0]);E=H()if inspect.isclass(H)else H;I=_B
				for D in G[1:]:
					if hasattr(E,D):
						F=getattr(E,D)
						if inspect.ismethod(F)or inspect.isfunction(F):
							J=inspect.signature(F);C={}
							for A in J.parameters.values():
								if A.default==inspect.Parameter.empty and A.name!=_J:
									if A.name==_K:
										if _L in D:C[A.name]=_M
										elif _N in D:C[A.name]=_O
										elif _P in D:C[A.name]=_Q
										elif _C in D:C[A.name]=_D
										else:C[A.name]=_R
									elif A.name==_C:C[A.name]=_D
									else:C[A.name]=_E
							try:E=F(**C)
							except Exception:I=_A;break
						else:E=F
					else:I=_A;break
				if I:B=E
		except Exception:pass
	if isinstance(B,str):print(f"Could not resolve documentation for: '{B}'");print("Tip: Use the object directly (if imported) or its name as a string (e.g., show_doc('Market')).");return
	try:J=inspect.signature(B);print(f"Signature: [92m{B.__name__}{J}[0m\n")
	except(ValueError,TypeError,AttributeError):pass
	K=inspect.getdoc(B)
	if K:print(K)
	else:M=getattr(B,_S,type(B).__name__);print(f"No documentation available for {M}.")
def show_api(layer=_E,show_navigation=_B):
	"\n    Displays a visual API Tree of available endpoints.\n    Only shows endpoint methods (returning data), hiding backward compatible aliases.\n    \n    Args:\n        layer: (Optional) Limit display to a specific Layer (e.g., Market(), 'Market'). \n               If empty (None), displays all 6 library layers.\n        show_navigation: If True, displays intermediate navigation methods (returning domain objects).\n                        Default is True.\n    ";R='\n\x1b[90mTip: Sử dụng show_doc(node) để đọc docstring.\x1b[0m';Q='Analytics';P='Fundamental';O='Insights';S='vnstock_data';G=show_navigation;E=layer;H=''
	if isinstance(E,str):
		try:
			from vnstock_data import ui;L=E.replace('()','').strip();I=L.split('.')
			if hasattr(ui,I[0]):
				J=getattr(ui,I[0])
				if inspect.isclass(J):B=J()
				else:B=J
				K=_B
				for D in I[1:]:
					if hasattr(B,D):
						F=getattr(B,D)
						if inspect.ismethod(F)or inspect.isfunction(F):
							T=inspect.signature(F);C={}
							for A in T.parameters.values():
								if A.default==inspect.Parameter.empty and A.name!=_J:
									if A.name==_K:
										if _L in D:C[A.name]=_M
										elif _N in D:C[A.name]=_O
										elif _P in D:C[A.name]=_Q
										elif _C in D:C[A.name]=_D
										else:C[A.name]=_R
									elif A.name==_C:C[A.name]=_D
									else:C[A.name]=_E
							try:B=F(**C)
							except Exception:K=_A;break
						else:B=F
					else:K=_A;break
				if K:E=B;H=L
		except Exception:pass
	def o(method):
		'Check if method returns a domain object (navigation, not data).'
		try:
			A=method.__annotations__.get(_G)
			if A:
				if isinstance(A,str):
					C=_I,_H,O,P,_F,Q
					if any(B in A for B in C):return _B
					return _A
				B=str(A)
				if _U not in B and _V not in B and'dict'not in B and'list'not in B:
					try:
						if A.__module__!='builtins':return _B
					except AttributeError:pass
			return _A
		except(AttributeError,TypeError):return _A
	def M(node,prefix='',is_last=_B,title='',level=0,show_nav=_A,parent_name='',title_suffix=''):
		n='property';m='method';l='...';k='│   ';j='    ';i='__class__';Z=show_nav;Y=level;U=is_last;T=prefix;R='├── ';Q='└── ';B=node
		if not hasattr(B,i)or type(B).__module__.split('.')[0]not in(S,'__main__'):return
		p=Q if U else R;q=title or(B.__name__ if hasattr(B,_S)else type(B).__name__);a=type(B).__name__==_F;V=parent_name or type(B).__name__;print(f"{T}{p}[96m{q}[0m{title_suffix}")
		if hasattr(B,i)and not inspect.isroutine(B):
			b=_get_public_methods(B,include_intermediate=_A,parent_name=V)
			for(W,(A,F))in enumerate(b):
				G=W==len(b)-1 if not Z else _A;H=T+(j if U else k);c=''
				try:
					N=F.__annotations__.get(_G)
					if N:
						if hasattr(N,_S):J=N.__name__
						else:
							J=str(N).replace('typing.','').replace('pandas.core.frame.','').replace('pandas.core.series.','')
							if'Optional'in J:J=J.replace('Optional[','').replace(']','')+' | None'
						c=f" -> [90m{J}[0m"
				except Exception:pass
				d=''
				try:
					if hasattr(B,'_domain_name')and hasattr(B,'_sources_config'):from vnstock_data.ui.config import get_route as r;s=r(B._domain_name,A,B._sources_config);d=f" [93m[{s[0].upper()}][0m"
				except Exception:pass
				e='';I=inspect.getdoc(F)
				if I:
					D=I.split('\n')[0].strip()
					if len(D)>100:D=D[:97]+l
					e=f" [90m# {D}[0m"
				K=Q if G else R;print(f"{H}{K}[92m{A}()[0m{d}{c}{e}")
			if Z:
				L=[]
				for(A,F)in inspect.getmembers(B,predicate=inspect.ismethod):
					if not _should_include_method(A,F,is_macro_layer=a,parent_name=V):continue
					if o(F):L.append((A,F,m))
				for(A,f)in inspect.getmembers(type(B)):
					if isinstance(f,property):
						if not _should_include_method(A,f,is_macro_layer=a,parent_name=V):continue
						try:
							X=getattr(B,A)
							if X is not _E and type(X).__module__.startswith(S):L.append((A,X,n))
						except Exception as g:pass
				L.sort(key=lambda x:x[0])
				for(W,(A,O,h))in enumerate(L):
					G=W==len(L)-1;H=T+(j if U else k);P=''
					if h==m:I=inspect.getdoc(O)
					else:t=getattr(type(B),A);I=inspect.getdoc(t)
					if I:
						D=I.split('\n')[0].strip()
						if len(D)>100:D=D[:97]+l
						P=f" [90m# {D}[0m"
					if h==n:M(O,H,G,A,Y+1,show_nav=_B,parent_name='',title_suffix=P)
					else:
						try:
							u=inspect.signature(O);E={}
							for C in u.parameters.values():
								if C.default==inspect.Parameter.empty and C.name!=_J:
									if C.name==_K:
										if _L in A:E[C.name]=_M
										elif _N in A:E[C.name]=_O
										elif _P in A:E[C.name]=_Q
										elif _C in A:E[C.name]=_D
										else:E[C.name]=_R
									elif C.name==_C:E[C.name]=_D
									else:E[C.name]=_E
							v=O(**E);M(v,H,G,A+'()',Y+1,show_nav=_B,parent_name='',title_suffix=P)
						except Exception as g:K=Q if G else R;print(f"{H}{K}[94m{A}()[0m{P}")
						except Exception as g:K=Q if G else R;print(f"{H}{K}[94m{A}()  [Navigation][0m")
	if E is not _E:U=f" - {H}"if H else'';print(f"\n[1mAPI STRUCTURE TREE{U}[0m");M(E,'',_B,'',0,show_nav=G)
	else:
		from vnstock_data.ui import Reference as V,Market as W,Insights as X,Fundamental as Y,Macro,Analytics as Z;print('\n\x1b[1mAPI STRUCTURE TREE - VNSTOCK_DATA (Unified UI Endpoints)\x1b[0m');print(S);N=[(_H,V()),(_I,W()),(P,Y()),(Q,Z()),(_F,Macro()),(O,X())]
		for(a,(b,B))in enumerate(N):c=a==len(N)-1;M(B,'',c,b,0,show_nav=G)
	if G:print(R);print('\x1b[90m[Navigation] = Intermediate methods returning domain objects\x1b[0m\n')
	else:print(R);print('\x1b[90mHint: show_api() để hiển thị cây đầy đủ với navigation methods.\x1b[0m\n')