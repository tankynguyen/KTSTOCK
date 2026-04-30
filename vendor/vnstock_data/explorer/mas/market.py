'Market module for MAS.'
_A='market'
from typing import Optional,Union
import pandas as pd
from vnai import agg_execution
from vnstock.core.utils.logger import get_logger
from vnstock.core.utils.parser import camel_to_snake
from vnstock_data.core.utils.client import send_request
from vnstock_data.core.utils.user_agent import get_headers
logger=get_logger(__name__)
class Market:
	'\n    Truy xuất thông tin trạng thái thị trường chung từ MAS.\n    '
	def __init__(A,random_agent=False,show_log=True):
		A.data_source='MAS';A.base_url='https://masboard.masvn.com/api/v1/market/';A.headers=get_headers(data_source=A.data_source,random_agent=random_agent)
		if not show_log:logger.setLevel('CRITICAL')
	@agg_execution('MAS.ext')
	def status(self,to_df=True,show_log=False):
		'\n        Lấy trạng thái thực tế của thị trường (ví dụ: OPEN, CLOSED, ATO, ATC)\n        Đầu ra là danh sách trạng thái các sàn HOSE, HNX, UPCOM.\n        \n        Tham số:\n            - to_df (tùy chọn): Chuyển đổi dữ liệu trả về dưới dạng DataFrame. Mặc định là True.\n            - show_log (tùy chọn): Hiển thị thông tin log giúp debug dễ dàng. Mặc định là False.\n        ';G='timestamp';F='asset_type';E='exchange';D='time';H=self.base_url+'marketStatus';C=send_request(url=H,headers=self.headers,method='GET',payload=None,show_log=show_log)
		if not C:raise ValueError('Không thể lấy dữ liệu trạng thái thị trường.')
		A=pd.DataFrame(C)
		for B in[D,'lastTradingDate','lastMarketInit']:
			if B in A.columns:A[B]=pd.to_datetime(A[B],unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Ho_Chi_Minh').dt.tz_localize(None)
		A.columns=[camel_to_snake(A)for A in A.columns];I={_A:E,'type':F,D:G};A=A.rename(columns=I);J=[E,F,'status',G,'last_trading_date'];A=A[[B for B in J if B in A.columns]]
		if to_df:return A
		return A.to_json(orient='records')
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register(_A,'mas',Market)