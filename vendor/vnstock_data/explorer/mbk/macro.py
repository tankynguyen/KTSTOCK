_O='interest_rate'
_N='exchange_rate'
_M='pivot'
_L='last_updated'
_K='quarter'
_J='%Y-%m-%d'
_I=True
_H='day'
_G='report_time'
_F='MBK'
_E=False
_D='year'
_C='group_name'
_B='month'
_A=None
import pandas as pd
from datetime import datetime,date
from typing import Optional,Union
from vnstock.core.utils.lookback import get_start_date_from_lookback
from vnai import agg_execution
from vnstock.core.utils.parser import camel_to_snake
from vnstock.core.utils.transform import reorder_cols
from vnstock_data.core.utils.client import send_request
from vnstock_data.core.utils.user_agent import get_headers
from vnstock_data.explorer.mbk.const import _BASE_URL,MACRO_DATA,REPORT_PERIOD,TYPE_ID
def process_report_dates(df,last_updated_col,keep_label=_I):
	"\n    Processes input series index to clean up and convert it to YYYY-mm-dd format.\n\n    Parameters:\n    df (pd.DataFrame): DataFrame whose index contains date information.\n    last_updated_col (str): Column name in df with the last updated dates (format 'YYYY-mm-dd' or datetime.date).\n    keep_label (bool): Whether to keep the original index as a column named 'original_index'.\n\n    Returns:\n    pd.DataFrame: DataFrame with two additional columns:\n        - report_time (converted to 'YYYY-mm-dd')\n        - report_type (extracted from original index)\n    ";N='9 tháng';M='6 tháng';I='Năm';B=df;J=[];K=[]
	for(F,G)in zip(B.index,B[last_updated_col]):
		if isinstance(G,date):L=G
		else:L=datetime.strptime(str(G),_J).date()
		if'/'in str(F):A,C=str(F).split('/');C=int(C)
		else:
			A=str(F)
			try:C=int(A);A=I
			except ValueError:raise ValueError(f"Unrecognized report type: {A}")
		if'Quý'in A:
			H=int(A.split(' ')[1]);O=H*3;D=date(C,O,1)
			if H==4 and L.year>C:D=date(C,12,31)
			E=f"Quý {H}"
		elif M in A:D=date(C,6,30);E=M
		elif N in A:D=date(C,9,30);E=N
		elif I in A or A.isdigit():D=date(C,12,31);E=I
		else:raise ValueError(f"Unrecognized report type: {A}")
		J.append(D.strftime(_J));K.append(E)
	B=B.copy()
	if keep_label:B['label']=B.index
	B.index=J;B['report_type']=K;return B
class Macro:
	"\n    A dedicated class for fetching macroeconomic data from MaybankTrade's API.\n\n    This class abstracts the common logic for retrieving macroeconomic data\n    (GDP, CPI, etc.) via a generalized data fetching method.\n\n    Attributes:\n        start (str): The default start period in the format 'YYYY-MM'.\n        end (str): The default end period in the format 'YYYY-MM'.\n        headers (dict): HTTP headers including a User-Agent for making requests.\n        show_log (bool): Flag to enable or disable logging for debugging.\n        data_source (str): Constant data source identifier ('MBK').\n\n    Methods:\n        _fetch_macro_data(indicator: str, start: str, end: str, period: str) -> pd.DataFrame:\n            Internal method to fetch and standardize data for a given indicator.\n        gdp(start: str, end: str, period: str) -> pd.DataFrame:\n            Fetches and returns standardized GDP data.\n        cpi(start: str, end: str, period: str) -> pd.DataFrame:\n            Fetches and returns standardized CPI data.\n    "
	def __init__(A,random_agent=_E,show_log=_E):'\n        Initializes the Macro class with a date range and API configuration.\n\n        Args:\n            random_agent (bool, optional): Use a random user agent if True. Defaults to False.\n            show_log (bool, optional): Toggle logging output. Defaults to False.\n        ';A.data_source=_F;A.headers=get_headers(data_source=A.data_source,random_agent=random_agent);A.headers['content-type']='application/x-www-form-urlencoded; charset=UTF-8';A.show_log=show_log
	def _fetch_macro_data(O,indicator,start=_A,end=_A,period=_K,length=_A):
		"\n        Internal method to fetch and process macroeconomic data for a given indicator.\n\n        This method validates the date inputs based on the indicator type,\n        constructs a raw-text payload, sends an API request, and processes the returned data.\n\n        Args:\n            indicator (str): The economic indicator key as defined in TYPE_ID (e.g., 'gdp', 'cpi', 'exchange_rate').\n            start (str): Start date. For 'exchange_rate', the format must be 'YYYY-mm-dd';\n                        for other indicators, the format must be 'YYYY-mm'.\n            end (str): End date. For 'exchange_rate', the format must be 'YYYY-mm-dd';\n                    for other indicators, the format must be 'YYYY-mm'.\n            period (str, optional): Report period type. Commonly 'quarter' or 'day'. Defaults to 'quarter'.\n\n        Raises:\n            ValueError: If the report period is unsupported, if date formats are invalid,\n                        or if the indicator code is not found in the TYPE_ID mapping.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized macroeconomic data with 'report_time' as the index.\n        ";W='Tháng ';P=start;N=indicator;M='0';L='-';I=length;F='';D=period;X=f"{_BASE_URL}{MACRO_DATA}";Q=REPORT_PERIOD.get(D)
		if Q is _A:raise ValueError(f"Unsupported report period type: {D}")
		if end is _A:B=datetime.now().strftime(_J)
		else:
			G=str(end)
			if len(G)==4 and G.isdigit():B=f"{G}-12-31"
			elif len(G)==7 and L in G:Y,Z=map(int,G.split(L));B=pd.Period(f"{Y}-{Z}",freq='M').end_time.strftime(_J)
			else:B=G
		if P is _A:
			if I is not _A:
				E=str(I).upper()
				if E.endswith('B'):E=E[:-1]+'D';C=get_start_date_from_lookback(lookback_length=E,end_date=B)
				elif E.isdigit():
					if D==_H:E+='D';C=get_start_date_from_lookback(lookback_length=E,end_date=B)
					else:C=get_start_date_from_lookback(lookback_length='20Y',end_date=B)
				else:C=get_start_date_from_lookback(lookback_length=E,end_date=B)
			else:a='1Y'if D==_H else'10Y';C=get_start_date_from_lookback(lookback_length=a,end_date=B)
		else:
			H=str(P)
			if len(H)==4 and H.isdigit():C=f"{H}-01-01"
			elif len(H)==7 and L in H:C=f"{H}-01"
			else:C=H
		R=C.split(L);S=B.split(L);b=R[0];c=S[0]
		if N in[_N,_O]and D==_H:J=C;K=B
		elif D==_D:J=M;K=M
		else:
			T=R[1];U=S[1]
			if D==_K:d=(int(T)-1)//3;e=(int(U)-1)//3;J=str(d);K=str(e)
			elif D==_B:J=str(int(T));K=str(int(U))
			else:J=M;K=M
		V=TYPE_ID.get(N)
		if V is _A:raise ValueError(f"{N} report type code is not defined in TYPE_ID mapping")
		f=f"type={Q}&fromYear={b}&toYear={c}&from={J}&to={K}&normTypeID={V}";g=send_request(url=X,headers=O.headers,method='POST',payload=f,show_log=O.show_log);A=pd.DataFrame(g);A.columns=[camel_to_snake(A)for A in A.columns];A.columns=A.columns.str.replace('tern_',F,regex=_E).str.replace('norm_',F,regex=_E).str.replace('term_',F,regex=_E).str.replace('from_',F,regex=_E).str.replace('_code',F,regex=_E)
		if _G in A.columns:A=A[A[_G]!=M].copy()
		h=pd.to_numeric(A[_H].str.replace('/Date(',F,regex=_E).str.replace(')/',F,regex=_E));A[_H]=pd.to_datetime(h,unit='ms').dt.date;i=['report_data_id','id',_D,'group_id','css_style','type_id'];A=A.drop(columns=i,errors='ignore');A=reorder_cols(A,cols=['unit','source'],position='last');A=reorder_cols(A,cols=[_G],position='first')
		if A[_G].str.contains(W).any():A[_G]=A[_G].str.replace(W,F,regex=_E);A[_G]=A[_G].apply(lambda x:pd.Period(x,freq='M').end_time.date()if isinstance(x,str)else x)
		A.set_index(_G,inplace=_I);A=A.sort_index(ascending=_I);A.rename(columns={_H:_L},inplace=_I)
		if I is not _A and str(I).isdigit():A=A.tail(int(I)).copy()
		return A
	@agg_execution(_F)
	def gdp(self,start=_A,end=_A,period=_K,keep_label=_E,length=_A):
		"\n        Fetches GDP data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized GDP data.\n        ";B=period
		if B not in[_K,_D]:raise ValueError(f"Unsupported report period type: {B}")
		A=self._fetch_macro_data('gdp',start,end,B,length=length);A=process_report_dates(A,last_updated_col=_L,keep_label=keep_label);A.index.name=_G;A=A.sort_values([_L,_C,'name']);return A
	@agg_execution(_F)
	def cpi(self,start=_A,end=_A,period=_B,length=_A):
		"\n        Fetches CPI data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized CPI data.\n        ";B=period
		if B not in[_B,_D]:raise ValueError(f"Unsupported report period type: {B}")
		A=self._fetch_macro_data('cpi',start,end,B,length=length)
		if _C in A.columns:A=A.drop(columns=[_C])
		return A
	@agg_execution(_F)
	def industry_prod(self,start=_A,end=_A,period=_B,length=_A):
		"\n        Fetches Industrial Production data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized Industrial Production data.\n        ";A=period
		if A not in[_B,_D]:raise ValueError(f"Unsupported report period type: {A}")
		return self._fetch_macro_data('industrial_production',start,end,A,length=length)
	@agg_execution(_F)
	def import_export(self,start=_A,end=_A,period=_B,length=_A):
		"\n        Fetches Import-Export data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized Import-Export data.\n        ";B=period
		if B not in[_B,_D]:raise ValueError(f"Unsupported report period type: {B}")
		A=self._fetch_macro_data('export_import',start,end,B,length=length)
		if _C in A.columns:A=A.drop(columns=[_C])
		return A
	@agg_execution(_F)
	def retail(self,start=_A,end=_A,period=_B,length=_A):
		"\n        Fetches Retail data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized Retail data.\n        ";B=period
		if B not in[_B,_D]:raise ValueError(f"Unsupported report period type: {B}")
		A=self._fetch_macro_data('retail',start,end,B,length=length)
		if _C in A.columns:A=A.drop(columns=[_C])
		return A
	@agg_execution(_F)
	def fdi(self,start=_A,end=_A,period=_B,length=_A):
		"\n        Fetches Foreign Direct Investment data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized Foreign Direct Investment data.\n        ";A=period
		if A not in[_B,_D]:raise ValueError(f"Unsupported report period type: {A}")
		return self._fetch_macro_data('fdi',start,end,A,length=length)
	@agg_execution(_F)
	def money_supply(self,start=_A,end=_A,period=_B,length=_A):
		"\n        Fetches money supply data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized Foreign Direct Investment data.\n        ";B=period
		if B not in[_B,_D]:raise ValueError(f"Unsupported report period type: {B}")
		A=self._fetch_macro_data('money_supply',start,end,B,length=length)
		if _C in A.columns:A=A.drop(columns=[_C])
		return A
	@agg_execution(_F)
	def interest_rate(self,start=_A,end=_A,period=_H,format=_M,length=_A):
		"\n        Fetches Interest Rate data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM-DD'. Defaults to '2025-01-02'.\n            end (str, optional): End date in the format 'YYYY-MM-DD'. Defaults to '2025-04-10'.\n            period (str, optional): Report period type. Defaults to 'day'.\n            format (str, optional): Format of the returned DataFrame. Options: 'pivot' (default wide table) or 'long' (raw flat table).\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized Interest Rate data.\n        ";B=period
		if B not in[_H,_D]:raise ValueError(f"Unsupported report period type: {B}")
		if format not in[_M,'long']:raise ValueError(f"Unsupported format type: {format}. Use 'pivot' or 'long'.")
		A=self._fetch_macro_data(_O,start,end,B,length=length);A.index=pd.to_datetime(A.index,dayfirst=_I)
		if format==_M:A=A.pivot_table(index=_G,columns=[_C,'name'],values='value');A=A.sort_index(axis=1,level=[0,1]);A=A.ffill()
		return A
	@agg_execution(_F)
	def exchange_rate(self,start=_A,end=_A,period=_H,length=_A):
		"\n        Fetches Real Interest exchange_rate data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized Real Interest exchange_rate data.\n        ";B=period
		if B not in[_H,_D]:raise ValueError(f"Unsupported report period type: {B}")
		A=self._fetch_macro_data(_N,start,end,B,length=length)
		if _C in A.columns:A=A.drop(columns=[_C])
		A.index=pd.to_datetime(A.index,dayfirst=_I);return A
	@agg_execution(_F)
	def population_labor(self,start=_A,end=_A,period=_D,length=_A):
		"\n        Fetches Population and Labor data for the specified period.\n\n        Args:\n            start (str, optional): Start date in the format 'YYYY-MM'. Defaults to '2015-01'.\n            end (str, optional): End date in the format 'YYYY-MM'. Defaults to '2025-04'.\n            period (str, optional): Report period type. Defaults to 'quarter'.\n\n        Returns:\n            pd.DataFrame: A DataFrame containing the standardized Population and Labor data.\n        ";B=period
		if B not in[_B,_D]:raise ValueError(f"Unsupported report period type: {B}")
		A=self._fetch_macro_data('population_labor',start,end,B,length=length)
		if _C in A.columns:A=A.drop(columns=[_C])
		return A
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('macro','mbk',Macro)