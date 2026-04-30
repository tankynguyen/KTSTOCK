_M='Failed to drop change column'
_L='change'
_K=False
_J='CafeF'
_I='TotalCount'
_H='%Y-%m-%d'
_G='index'
_F='%d/%m/%Y'
_E='GET'
_D=True
_C='%m/%d/%Y'
_B=None
_A='Data'
import requests,pandas as pd
from typing import Union,Optional,Dict
from vnstock_data.explorer.cafef.const import _BASE_URL,_PRICE_HISTORY_MAP,_FOREIGN_TRADE_MAP,_PROP_TRADE_MAP,_ORDER_STATS_MAP,_INSIDER_DEAL_MAP,_CAFEF_INDEX_MAPPING,_CAFEF_INDEX_BASE_URL,_INDEX_PRICE_HISTORY_MAP,_INDEX_FOREIGN_TRADE_MAP,_INDEX_ORDER_STATS_MAP
from vnstock_data.core.utils.parser import days_between
from vnstock_data.core.utils.user_agent import get_headers
from vnstock.core.utils.logger import get_logger
logger=get_logger(__name__)
class Trading:
	def __init__(A,symbol,random_agent=_K,asset_type='equity',**B):
		A.asset_type=asset_type;A.raw_symbol=symbol.upper()
		if A.asset_type==_G:
			if A.raw_symbol not in _CAFEF_INDEX_MAPPING:raise ValueError(f"Mã chỉ số '{A.raw_symbol}' không được hỗ trợ bởi nguồn CafeF. Các mã hợp lệ: VNINDEX (HOSE), UPCOMINDEX (UPCOM), HNXINDEX (HNX), VN30.")
			A.symbol=_CAFEF_INDEX_MAPPING[A.raw_symbol]
		else:A.symbol=A.raw_symbol
		A.base_url=_BASE_URL;A.headers=get_headers(data_source='CAFEF',random_agent=random_agent)
	def _df_standardized(F,history_data,mapping_dict):
		'\n        Định dạng lại dữ liệu lịch sử giá của mã chứng khoán\n        ';C=mapping_dict;B='time';A=history_data;A=A.rename(columns=C);D=C.values()
		if A.empty:logger.info('No data found');return
		else:
			try:A=A[D]
			except Exception as G:logger.debug(f"Failed to sort column names. Actual columns and predefine mapping dict mismatched. Actual columns: {A.columns}. Expected columns: {D}");pass
			if B in A.columns:
				if A[B].astype(str).str.contains('/Date\\(',regex=_D).any():E=A[B].astype(str).str.replace('\\D','',regex=_D);A[B]=pd.to_datetime(pd.to_numeric(E),unit='ms')
				else:A[B]=pd.to_datetime(A[B],format=_F)
				A.set_index(B,inplace=_D)
			return A
	def price_history(B,start,end,page=1,limit=_B):
		"\n        Truy xuất dữ liệu lịch sử giá của mã chứng khoán/chỉ số bất kỳ từ nguồn dữ liệu CafeF\n\n        Tham số:\n            - start (bắt buộc): Ngày bắt đầu lấy dữ liệu, định dạng YYYY-mm-dd. Ví dụ '2024-06-01'.\n            - end (bắt buộc): Ngày kết thúc lấy dữ liệu, định dạng YYYY-mm-dd. Ví dụ '2024-07-31'.\n            - page (tùy chọn): Trang hiện tại. Mặc định là 1.\n            - limit (tùy chọn): Số lượng dữ liệu trả về trong một lần request. Mặc định là None.\n        Return:\n            - DataFrame: Dữ liệu lịch sử giá của mã chứng khoán/chỉ số.\n        ";N='ThayDoi';H=limit;G=end;F=start;E='ListDataLSG'
		if H is _B:H=days_between(start=F,end=G,format=_H)
		if B.asset_type==_G:
			I=pd.to_datetime(F).strftime(_F);J=pd.to_datetime(G).strftime(_F);K=f"{_CAFEF_INDEX_BASE_URL}/LichSuGia.ashx?TradeCenter={B.symbol}&StartDate={I}&EndDate={J}";C=requests.request(_E,K,headers=B.headers)
			if C.status_code!=200:raise ConnectionError(f"Tải dữ liệu không thành công: {C.status_code} - {C.text}")
			D=C.json()
			if _A not in D or E not in D[_A]or D[_A][E]is _B:logger.error(f"Dữ liệu không hợp lệ từ CafeF: {D}");return
			L=len(D[_A][E]);logger.info(f"Lịch sử giá chỉ số:\nMã CK (Index): {B.symbol}. Số bản ghi hợp lệ: {L}");A=pd.DataFrame(D[_A][E])
			try:A=B._df_standardized(A,_INDEX_PRICE_HISTORY_MAP)
			except Exception as M:logger.error(f"Failed to standardize data: {M}")
		else:
			I=pd.to_datetime(F).strftime(_C);J=pd.to_datetime(G).strftime(_C);K=f"{B.base_url}/PriceHistory.ashx?Symbol={B.symbol}&StartDate={I}&EndDate={J}&PageIndex={page}&PageSize={H}";C=requests.request(_E,K,headers=B.headers)
			if C.status_code!=200:raise ConnectionError(f"Tải dữ liệu không thành công: {C.status_code} - {C.text}")
			D=C.json()[_A];L=D[_I];logger.info(f"Lịch sử giá:\nMã CK: {B.symbol}. Số bản ghi hợp lệ: {L}");A=pd.DataFrame(D[_A])
			try:
				if N in A.columns:A['change_pct']=pd.to_numeric(A[N].str.split('(',expand=_D)[1].str.replace(' %)','',regex=_K).str.replace(')','',regex=_K).str.strip(),errors='coerce')/100
			except:logger.debug('Failed to extract change_pct from ThayDoi column');pass
			try:A=B._df_standardized(A,_PRICE_HISTORY_MAP)
			except Exception as M:logger.error(f"Failed to standardize data: {M}")
		try:A.drop(columns=[_L],inplace=_D)
		except:logger.debug(_M);pass
		A.name=B.symbol;A.category='history_price';A.source=_J;return A
	def foreign_trade(A,start,end,page=1,limit=_B):
		'\n        Truy xuất dữ liệu lịch sử giao dịch nhà đầu tư nước ngoài của mã chứng khoán/chỉ số bất kỳ từ nguồn dữ liệu CafeF\n        ';H=limit;G=end;F=start;E='ListDataNN'
		if H is _B:H=days_between(start=F,end=G,format=_H)
		if A.asset_type==_G:
			I=pd.to_datetime(F).strftime(_F);J=pd.to_datetime(G).strftime(_F);K=f"{_CAFEF_INDEX_BASE_URL}/GDNuocNgoai.ashx?TradeCenter={A.symbol}&StartDate={I}&EndDate={J}";C=requests.request(_E,K,headers=A.headers)
			if C.status_code!=200:raise ConnectionError(f"Tải dữ liệu không thành công: {C.status_code} - {C.text}")
			D=C.json()
			if _A not in D or E not in D[_A]or D[_A][E]is _B:return
			L=len(D[_A][E]);logger.info(f"Lịch sử GD Nước ngoài chỉ số:\nMã CK (Index): {A.symbol}. Số bản ghi hợp lệ: {L}");B=pd.DataFrame(D[_A][E]);B=A._df_standardized(B,_INDEX_FOREIGN_TRADE_MAP)
		else:
			I=pd.to_datetime(F).strftime(_C);J=pd.to_datetime(G).strftime(_C);K=f"{A.base_url}/GDKhoiNgoai.ashx?Symbol={A.symbol}&StartDate={I}&EndDate={J}&PageIndex={page}&PageSize={H}";C=requests.request(_E,K,headers=A.headers)
			if C.status_code!=200:raise ConnectionError(f"Tải dữ liệu không thành công: {C.status_code} - {C.text}")
			D=C.json()[_A];L=D[_I];logger.info(f"Lịch sử GD Nước ngoài:\nMã CK: {A.symbol}. Số bản ghi hợp lệ: {L}");B=pd.DataFrame(D[_A]);B=A._df_standardized(B,_FOREIGN_TRADE_MAP)
		try:B.drop(columns=[_L],inplace=_D)
		except:logger.debug(_M);pass
		B.name=A.symbol;B.category='foreign_trade';B.source=_J;return B
	def prop_trade(A,start,end,page=1,limit=_B):
		'\n        Truy xuất dữ liệu lịch sử giao dịch tự doanh (chỉ hỗ trợ cổ phiếu) từ nguồn dữ liệu CafeF\n        ';E=start;D=limit
		if A.asset_type==_G:raise ValueError('API CafeF không hỗ trợ dữ liệu giao dịch tự doanh cho đối tượng chỉ số.')
		if D is _B:D=days_between(start=E,end=end,format=_H)
		G=pd.to_datetime(E).strftime(_C);H=pd.to_datetime(end).strftime(_C);I=f"{A.base_url}/GDTuDoanh.ashx?Symbol={A.symbol}&StartDate={G}&EndDate={H}&PageIndex={page}&PageSize={D}";C=requests.request(_E,I,headers=A.headers)
		if C.status_code!=200:raise ConnectionError(f"Tải dữ liệu không thành công: {C.status_code} - {C.text}")
		F=C.json()[_A];J=F[_I];logger.info(f"Lịch sử GD Tự Doanh:\nMã CK: {A.symbol}. Số bản ghi hợp lệ: {J}");B=pd.DataFrame(F[_A]['ListDataTudoanh']);B=A._df_standardized(B,_PROP_TRADE_MAP)
		try:B.drop(columns='symbol',inplace=_D)
		except:logger.debug('Failed to drop symbol column');pass
		B.name=A.symbol;B.category='prop_trade';B.source=_J;return B
	def order_stats(A,start,end,page=1,limit=_B):
		'\n        Truy xuất dữ liệu lịch sử thống kê đặt lệnh của mã chứng khoán/chỉ số bất kỳ từ nguồn dữ liệu CafeF\n        ';H=limit;G=end;F=start;E='ListDataTKDL'
		if H is _B:H=days_between(start=F,end=G,format=_H)
		if A.asset_type==_G:
			I=pd.to_datetime(F).strftime(_F);J=pd.to_datetime(G).strftime(_F);K=f"{_CAFEF_INDEX_BASE_URL}/ThongKeDL.ashx?TradeCenter={A.symbol}&StartDate={I}&EndDate={J}";C=requests.request(_E,K,headers=A.headers)
			if C.status_code!=200:raise ConnectionError(f"Tải dữ liệu không thành công: {C.status_code} - {C.text}")
			D=C.json()
			if _A not in D or E not in D[_A]or D[_A][E]is _B:return
			L=len(D[_A][E]);logger.info(f"Thống kê đặt lệnh chỉ số:\nMã CK (Index): {A.symbol}. Số bản ghi hợp lệ: {L}");B=pd.DataFrame(D[_A][E]);B=A._df_standardized(B,_INDEX_ORDER_STATS_MAP)
		else:
			I=pd.to_datetime(F).strftime(_C);J=pd.to_datetime(G).strftime(_C);K=f"{A.base_url}/ThongKeDL.ashx?Symbol={A.symbol}&StartDate={I}&EndDate={J}&PageIndex={page}&PageSize={H}";C=requests.request(_E,K,headers=A.headers)
			if C.status_code!=200:raise ConnectionError(f"Tải dữ liệu không thành công: {C.status_code} - {C.text}")
			D=C.json()[_A];L=D[_I];logger.info(f"Thống kê đặt lệnh:\nMã CK: {A.symbol}. Số bản ghi hợp lệ: {L}");B=pd.DataFrame(D[_A]);B=A._df_standardized(B,_ORDER_STATS_MAP)
		try:B.drop(columns=[_L],inplace=_D)
		except:logger.debug(_M);pass
		B.name=A.symbol;B.category='order_stats';B.source=_J;return B
	def insider_deal(B,start,end,page=1,limit=_B):
		'\n        Truy xuất dữ liệu lịch sử thống kê giao dịch của cổ đông & nội bộ (chỉ hỗ trợ cổ phiếu) từ nguồn dữ liệu CafeF\n        ';F=start;E=limit
		if B.asset_type==_G:raise ValueError('API CafeF không hỗ trợ thống kê dữ liệu cổ đông nội bộ cho đối tượng chỉ số.')
		if E is _B:E=days_between(start=F,end=end,format=_H)
		H=pd.to_datetime(F).strftime(_C);I=pd.to_datetime(end).strftime(_C);J=f"{B.base_url}/GDCoDong.ashx?Symbol={B.symbol}&StartDate={H}&EndDate={I}&PageIndex={page}&PageSize={E}";C=requests.request(_E,J,headers=B.headers)
		if C.status_code!=200:raise ConnectionError(f"Tải dữ liệu không thành công: {C.status_code} - {C.text}")
		G=C.json()[_A];K=G[_I];logger.info(f"Thống kê giao dịch Cổ Đông & Nội bộ:\nMã CK: {B.symbol}. Số bản ghi hợp lệ: {K}");A=pd.DataFrame(G[_A]);A=B._df_standardized(A,_INSIDER_DEAL_MAP)
		for D in['plan_begin_date','plan_end_date','real_end_date','published_date','order_date']:A[D]=A[D].str.replace('\\D','',regex=_D);A[D]=pd.to_datetime(pd.to_numeric(A[D]),unit='ms')
		A.name=B.symbol;A.category='insider_deals';A.source=_J;return A
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('trading','cafef',Trading)