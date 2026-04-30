'Listing module for ForexSB.'
_C='FXSB.ext'
_B=True
_A=False
import json,gzip
from typing import Dict,Optional,Union
import pandas as pd
from vnstock.core.utils.logger import get_logger
from vnai import agg_execution
logger=get_logger(__name__)
from vnstock_data.core.utils.user_agent import get_headers
class Listing:
	'\n    Cấu hình truy cập danh sách symbol từ ForexSB.\n    '
	def __init__(A,random_agent=_A,show_log=_A):
		B=show_log;A.data_source='FXSB';A.base_url='https://data.forexsb.com/datafeed/info/premium.json.gz';A.show_log=B
		if not B:logger.setLevel('CRITICAL')
	@agg_execution(_C)
	def all_symbols(self,show_log=_A,to_df=_B):
		'\n        Truy xuất danh sách các mã hỗ trợ (Forex, Crypto, v.v) từ ForexSB.\n        ';import requests as E;A=E.get(self.base_url,headers=get_headers('FXSB',random_agent=_A,browser='chrome',platform='macos'))
		if A.status_code!=200:raise ValueError(f"Không thể truy cập dữ liệu symbol từ ForexSB. Status: {A.status_code}")
		try:
			if A.content[:2]==b'\x1f\x8b':C=gzip.decompress(A.content)
			else:C=A.content
			F=json.loads(C)
		except Exception as G:raise ValueError(f"Lỗi khi giải nén hoặc parse dữ liệu: {G}")
		B=F
		if show_log:logger.info(f"Tìm thấy {len(B)} biểu tượng.")
		if to_df:H=list(B.values());D=pd.DataFrame(H);D.source=self.data_source;return D
		else:return B
	@agg_execution(_C)
	def search_symbol(self,query,show_log=_A,to_df=_B):
		'\n        Tìm kiếm các mã hỗ trợ trên ForexSB dựa vào từ khóa (tìm theo symbol hoặc description).\n        \n        Tham số:\n            - query (str): Từ khóa tìm kiếm.\n            - show_log (bool): Hiển thị log dữ liệu.\n            - to_df (bool): Trả về DataFrame hay JSON string.\n        ';D=to_df;C=query;A=self.all_symbols(show_log=_A,to_df=_B)
		if A.empty:
			if not D:return'[]'
			return A
		E=C.lower();F=A['symbol'].str.lower().str.contains(E,na=_A)|A['description'].str.lower().str.contains(E,na=_A);B=A[F].reset_index(drop=_B)
		if show_log:logger.info(f"Tìm thấy {len(B)} kết quả khớp với từ khóa '{C}'")
		if D:return B
		else:return B.to_json(orient='records')
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('listing','fxsb',Listing)