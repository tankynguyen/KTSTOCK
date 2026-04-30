'\nDukascopy Provider – Listing module.\n\nInstrument discovery for the Dukascopy data feed.\nAll symbols from https://jetta.dukascopy.com/v1/instruments,\norganized and searchable by code, description, or instrument type.\n\nSupported instrument types:\n  FX    – Forex currency pairs (EUR-USD, USD-JPY, GBP-USD…)\n  IDX   – Global indices (USA500.IDX-USD, GER30.IDX-EUR, JPN225.IDX-JPY…)\n  CMD   – Commodities (XAUUSD.CMD-USD, XAGUSD.CMD-USD, COFFEE.CMD-USX…)\n  STK   – Individual stocks (AAPL.NYSE-USD, META.NSD-USD…)\n  CFD   – Contract-for-Difference instruments\n  CRYPTO– Cryptocurrencies (BTCUSD, ETHUSD…)\n'
_F='Dukascopy.ext'
_E='symbol'
_D='description'
_C='code'
_B=True
_A=False
from typing import Optional,Union
import re as _re,pandas as pd,requests
from vnstock.core.utils.logger import get_logger
from vnstock_data.core.utils.user_agent import get_headers
from vnai import agg_execution
logger=get_logger(__name__)
from vnstock_data.explorer.dukas.const import _BASE_URL,_SYMBOL_SUFFIX_PATTERN,_PLATFORM_GROUP_MAP
_SUFFIX_RE=_re.compile(_SYMBOL_SUFFIX_PATTERN)
def _clean_code(code):'Return user-friendly symbol: strip exchange/asset-class suffixes and hyphens.\n    e.g. EUR-USD -> EURUSD.\n    ';A=_SUFFIX_RE.sub('',code);return A.replace('-','')
class Listing:
	"\n    Dukascopy instrument discovery.\n\n    Retrieves the full catalogue from ``GET /v1/instruments``\n    and provides filtering/search utilities.\n\n    Supported instrument types\n    ──────────────────────────\n    FX      Currency pairs        EUR-USD, USD-JPY, GBP-USD\n    IDX     Global indices        USA500.IDX-USD, GER30.IDX-EUR\n    CMD     Commodities           XAUUSD.CMD-USD, COFFEE.CMD-USX\n    STK     Individual stocks     AAPL.NYSE-USD, META.NSD-USD\n    CFD     CFDs\n    CRYPTO  Cryptocurrencies      BTCUSD, ETHUSD\n\n    Example\n    -------\n    >>> from vnstock_data import Reference\n    >>> ref = Reference()\n    >>> ref.instruments().all_symbols(instrument_type='IDX')\n    "
	def __init__(A,show_log=_A,**C):
		B=show_log;A.data_source='Dukascopy';A.base_url=_BASE_URL;A.show_log=B
		if not B:logger.setLevel('CRITICAL')
	def _fetch_instruments(C):
		try:B=requests.get(f"{C.base_url}/instruments",headers=get_headers('DUKASCOPY',random_agent=_A,browser='chrome',platform='macos'),timeout=15)
		except requests.exceptions.Timeout:raise ConnectionError('Dukascopy instruments request timed out (15s). Check network.')
		except requests.exceptions.RequestException as D:raise ConnectionError(f"Dukascopy connection error: {D}")
		if B.status_code!=200:raise ValueError(f"Dukascopy instruments error: HTTP {B.status_code}")
		A=B.json();return A.get('instruments',A)if isinstance(A,dict)else A
	@agg_execution(_F)
	def all_symbols(self,instrument_type=None,to_df=_B):
		"\n        Retrieve the full instrument catalogue from Dukascopy.\n\n        Args:\n            instrument_type (str | None): Filter by type – ``'FX'``, ``'IDX'``,\n                ``'CMD'``, ``'STK'``, ``'CFD'``, ``'CRYPTO'``. ``None`` = all.\n            to_df (bool): Return DataFrame (default) or raw list.\n\n        Returns:\n            pd.DataFrame: Schema ``[code, name, description, type, country_code,\n                pip_value, price_scale]``\n        ";I='type';H='name';D=instrument_type;C=self;J=C._fetch_instruments();B=[]
		for A in J:E=A.get('platformGroupId','');K=_PLATFORM_GROUP_MAP.get(E,E);F=A.get(_C,'');B.append({_E:_clean_code(F),_C:F,H:A.get(H,''),_D:A.get(_D,'')or'',I:K,'country_code':A.get('countryCode',''),'pip_value':A.get('pipValue'),'price_scale':A.get('priceScale')})
		if D:L=D.upper();B=[A for A in B if A[I]==L]
		M=D or'all'
		if C.show_log:logger.info(f"Dukascopy: {len(B)} instruments found (type={M})")
		if not to_df:return B
		G=pd.DataFrame(B);G.source=C.data_source;return G
	@agg_execution(_F)
	def search_symbol(self,query,instrument_type=None,to_df=_B):
		'\n        Search instruments by keyword (matches code or description).\n\n        Args:\n            query (str): Search keyword.\n            instrument_type (str | None): Optional type filter.\n            to_df (bool): Return DataFrame or raw list.\n\n        Returns:\n            pd.DataFrame: Filtered instrument list.\n        ';D=query;A=self.all_symbols(instrument_type=instrument_type,to_df=_B)
		if A.empty:return A
		B=D.lower();E=A[_E].str.lower().str.contains(B,na=_A)|A[_C].str.lower().str.contains(B,na=_A)|A[_D].str.lower().str.contains(B,na=_A);C=A[E].reset_index(drop=_B)
		if self.show_log:logger.info(f"Dukascopy search '{D}': {len(C)} results")
		if not to_df:return C.to_dict('records')
		return C
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('listing','dukascopy',Listing)