'Listing module.'
_O="Tham số lang phải là 'vi' hoặc 'en'."
_N='name'
_M='Không tìm thấy dữ liệu. Vui lòng kiểm tra lại.'
_L='data'
_K='icb_name'
_J='GET'
_I='organ_name'
_H='records'
_G='VCI'
_F='vi'
_E='symbol'
_D='icb_code'
_C='VCI.ext'
_B=False
_A=True
from typing import Dict,Optional
from datetime import datetime
from vnstock.explorer.vci.const import _GROUP_CODE,_TRADING_URL,_GRAPHQL_URL
import json,pandas as pd
from vnstock.core.utils.parser import camel_to_snake
from vnstock.core.utils.logger import get_logger
from vnstock.core.utils.transform import drop_cols_by_pattern,reorder_cols
from vnstock_data.core.utils.client import send_request
from vnstock_data.core.utils.user_agent import get_headers
from vnai import agg_execution
logger=get_logger(__name__)
class Listing:
	'\n    Cấu hình truy cập dữ liệu lịch sử giá chứng khoán từ VCI.\n    '
	def __init__(A,random_agent=_B,show_log=_B):
		B=show_log;A.data_source=_G;A.base_url=_TRADING_URL;A.headers=get_headers(data_source=A.data_source,random_agent=random_agent);A.show_log=B
		if not B:logger.setLevel('CRITICAL')
	@agg_execution(_C)
	def all_symbols(self,show_log=_B,to_df=_A):
		'\n        Truy xuất danh sách toàn. bộ mã và tên các cổ phiếu trên thị trường Việt Nam.\n\n        Tham số:\n            - show_log (tùy chọn): Hiển thị thông tin log giúp debug dễ dàng. Mặc định là False.\n            - to_df (tùy chọn): Chuyển đổi dữ liệu danh sách mã cổ phiếu trả về dưới dạng DataFrame. Mặc định là True. Đặt là False để trả về dữ liệu dạng JSON.\n        ';A=self.symbols_by_exchange(show_log=show_log,to_df=_A);A=A.query('type == "STOCK"').reset_index(drop=_A);A=A[[_E,_I]]
		if to_df:return A
		else:B=A.to_json(orient=_H);return B
	@agg_execution(_C)
	def symbols_by_industries(self,lang=_F,show_log=_B,to_df=_A):
		'\n        Truy xuất thông tin phân ngành icb của các mã cổ phiếu trên thị trường Việt Nam.\n\n        Tham số:\n            - show_log (tùy chọn): Hiển thị thông tin log giúp debug dễ dàng. Mặc định là False.\n            - to_df (tùy chọn): Chuyển đổi dữ liệu danh sách mã cổ phiếu trả về dưới dạng DataFrame. Mặc định là True. Đặt là False để trả về dữ liệu dạng JSON.\n        ';J='com_type_code';I='code';F=show_log;E='icb_level'
		if lang not in[_F,'en']:raise ValueError(_O)
		K='1'if lang==_F else'2';L=f"https://iq.vietcap.com.vn/api/iq-insight-service/v2/company/search-bar?language={K}";C=send_request(url=L,headers=self.headers,method=_J,show_log=F)
		if not C or _L not in C:raise ValueError(_M)
		if F:logger.info(f"Truy xuất thành công dữ liệu danh sách phân ngành icb.")
		G=[]
		for B in C[_L]:
			M=B.get(I);N=B.get(_N);O=B.get('comTypeCode')
			for H in range(1,5):
				D=f"icbLv{H}"
				if D in B and B[D]is not None:G.append({_E:M,_I:N,J:O,E:H,_D:B[D].get(I),_K:B[D].get(_N)})
		A=pd.DataFrame(G)
		if not A.empty:A=A[A[_D].notna()&(A[_D]!='')];A=A.sort_values(by=[_E,E]).reset_index(drop=_A);A=A[[_E,_I,J,E,_D,_K]]
		A.source=_G
		if to_df:return A
		else:C=A.to_json(orient=_H);return C
	@agg_execution(_C)
	def symbols_by_exchange(self,lang=_F,show_log=_B,to_df=_A):
		'\n        Truy xuất thông tin niêm yết theo sàn của các mã cổ phiếu trên thị trường Việt Nam.\n\n        Tham số:\n                - show_log (tùy chọn): Hiển thị thông tin log giúp debug dễ dàng. Mặc định là False.\n                - to_df (tùy chọn): Chuyển đổi dữ liệu danh sách mã cổ phiếu trả về dưới dạng DataFrame. Mặc định là True. Đặt là False để trả về dữ liệu dạng JSON.\n        ';E='en_';D='exchange';C=show_log
		if lang not in[_F,'en']:raise ValueError(_O)
		F=self.base_url+'/price/symbols/getAll';B=send_request(url=F,headers=self.headers,method=_J,payload=None,show_log=C)
		if not B:raise ValueError(_M)
		if C:logger.info(f"Truy xuất dữ liệu thành công cho {len(B)} mã.")
		A=pd.DataFrame(B);A.columns=[camel_to_snake(A)for A in A.columns];A=A.rename(columns={'board':D});A=reorder_cols(A,[_E,D,'type'],position='first');A=A.drop(columns=['id'])
		if lang==_F:A=drop_cols_by_pattern(A,[E])
		else:A=A.drop(columns=[_I,'organ_short_name']);A.columns=[A.replace(E,'')for A in A.columns]
		if to_df:A.source=_G;return A
		else:B=A.to_json(orient=_H);return B
	@agg_execution(_C)
	def industries_icb(self,show_log=_B,to_df=_A):
		'\n        Truy xuất thông tin phân ngành icb của các mã cổ phiếu trên thị trường Việt Nam.\n\n        Tham số:\n            - show_log (tùy chọn): Hiển thị thông tin log giúp debug dễ dàng. Mặc định là False.\n            - to_df (tùy chọn): Chuyển đổi dữ liệu danh sách mã cổ phiếu trả về dưới dạng DataFrame. Mặc định là True. Đặt là False để trả về dữ liệu dạng JSON.\n        ';E='level';D='en_icb_name';C=show_log;F='https://iq.vietcap.com.vn/api/iq-insight-service/v1/sectors/icb-codes';B=send_request(url=F,headers=self.headers,method=_J,show_log=C)
		if not B:raise ValueError(_M)
		if C:logger.info(f"Truy xuất thành công dữ liệu danh sách phân ngành icb.")
		A=pd.DataFrame(B[_L]);A=A.rename(columns={_N:_D,'viSector':_K,'enSector':D,'icbLevel':E})
		if not A.empty:A=A[[_K,D,_D,E]];A=A.sort_values(by=[_D]).reset_index(drop=_A)
		A.source=_G
		if to_df:return A
		else:B=A.to_json(orient=_H);return B
	@agg_execution(_C)
	def symbols_by_group(self,group='VN30',show_log=_B,to_df=_A):
		"\n        Truy xuất danh sách các mã cổ phiếu theo tên nhóm trên thị trường Việt Nam.\n\n        Tham số:\n            - group (tùy chọn): Tên nhóm cổ phiếu. Mặc định là 'VN30'. Các mã có thể là: HOSE, VN30, VNMidCap, VNSmallCap, VNAllShare, VN100, ETF, HNX, HNX30, HNXCon, HNXFin, HNXLCap, HNXMSCap, HNXMan, UPCOM, FU_INDEX (mã chỉ số hợp đồng tương lai), CW (chứng quyền).\n            - show_log (tùy chọn): Hiển thị thông tin log giúp debug dễ dàng. Mặc định là False.\n            - to_df (tùy chọn): Chuyển đổi dữ liệu danh sách mã cổ phiếu trả về dưới dạng DataFrame. Mặc định là True. Đặt là False để trả về dữ liệu dạng JSON.\n        ";D=show_log;C=group
		if C not in _GROUP_CODE:raise ValueError(f"Invalid group. Group must be in {_GROUP_CODE}")
		E=self.base_url+f"/price/symbols/getByGroup?group={C}";A=send_request(url=E,headers=self.headers,method=_J,payload=None,show_log=D)
		if D:logger.info(f"Truy xuất thành công dữ liệu danh sách mã CP theo nhóm.")
		B=pd.DataFrame(A)
		if to_df:
			if not A:raise ValueError('JSON data is empty or not provided.')
			B.source=_G;return B[_E]
		else:A=B.to_json(orient=_H);return A
	@agg_execution(_C)
	def all_future_indices(self,show_log=_B,to_df=_A):return self.symbols_by_group(group='FU_INDEX',show_log=show_log,to_df=to_df)
	@agg_execution(_C)
	def all_government_bonds(self,show_log=_B,to_df=_A):return self.symbols_by_group(group='FU_BOND',show_log=show_log,to_df=to_df)
	@agg_execution(_C)
	def all_covered_warrant(self,show_log=_B,to_df=_A):return self.symbols_by_group(group='CW',show_log=show_log,to_df=to_df)
	@agg_execution(_C)
	def all_bonds(self,show_log=_B,to_df=_A):return self.symbols_by_group(group='BOND',show_log=show_log,to_df=to_df)
	@agg_execution(_C)
	def all_etf(self,show_log=_B,to_df=_A):'\n        Truy xuất danh sách mã quỹ ETF.\n        ';return self.symbols_by_group(group='ETF',show_log=show_log,to_df=to_df)
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('listing','vci',Listing)