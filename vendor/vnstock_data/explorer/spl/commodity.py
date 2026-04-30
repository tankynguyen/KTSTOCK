_D='commodity'
_C='close'
_B='SPL.ext'
_A=None
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from.spl_fetcher import SPLFetcher
from typing import Dict,Any,Optional,List,Union
from datetime import timedelta
from vnstock.core.utils.lookback import get_start_date_from_lookback
from vnai import agg_execution
from vnstock.core.utils.logger import get_logger
logger=get_logger(__name__)
class CommodityPrice:
	'\n    Lớp cung cấp các phương thức để lấy dữ liệu giá hàng hóa từ nguồn SPL.\n    '
	def __init__(A,start=_A,end=_A,length=_A,show_log=False):
		"\n        Khởi tạo đối tượng CommodityPrice với tùy chọn ngày bắt đầu và kết thúc mặc định.\n\n        Các tham số:\n            start (str, optional): Ngày bắt đầu mặc định (định dạng 'YYYY-MM-DD'). Mặc định là None.\n            end (str, optional): Ngày kết thúc mặc định (định dạng 'YYYY-MM-DD'). Mặc định là None.\n            length (str, int, optional): Khoảng thời gian mặc định cần lấy dữ liệu. Mặc định là '1Y'.\n        ";B=length;A.fetcher=SPLFetcher();A.default_start=start;A.default_end=end;A.default_length=B if B is not _A else'1Y'
		if not show_log:logger.setLevel('CRITICAL')
	def _fetch_commodity(C,ticker,start=_A,end=_A,interval='1d',columns=_A,length=_A):
		"\n        Lấy dữ liệu giá hàng hóa từ API SPL.\n\n        Các tham số:\n            ticker (str): Mã hàng hóa cần lấy dữ liệu.\n            start (str, optional): Ngày bắt đầu (định dạng 'YYYY-MM-DD').\n                Ưu tiên tham số nếu có, mặc định là giá trị khởi tạo.\n            end (str, optional): Ngày kết thúc (định dạng 'YYYY-MM-DD').\n                Ưu tiên tham số nếu có, mặc định là giá trị khởi tạo.\n            interval (str, optional): Khoảng thời gian (mặc định '1d').\n            columns (List, optional): Danh sách cột cần lấy.\n                Mặc định là None (lấy tất cả).\n        \n        Giá trị trả về:\n            pd.DataFrame: Dữ liệu giá hàng hóa với time làm index.\n        ";P=columns;O='%Y-%m-%d';H=end;G=start;D=length;B='time';E=H or C.default_end
		if E is _A:E=datetime.now().strftime(O)
		F=G
		if F is _A:
			L=D if D is not _A else C.default_length
			if L is not _A:
				if str(L).isdigit():F=get_start_date_from_lookback(lookback_length='20Y',end_date=E)
				else:
					I=str(L).upper()
					if I.endswith('B'):I=I[:-1]+'D'
					F=get_start_date_from_lookback(lookback_length=I,end_date=E)
			else:F=C.default_start
		J={'ticker':ticker,'interval':interval,'type':_D};K=ZoneInfo('Asia/Ho_Chi_Minh');G=F;H=E
		if G:M=datetime.strptime(G,O);M=M.replace(hour=0,minute=0,second=0,microsecond=0,tzinfo=K);J['from']=int(M.timestamp())
		if H:N=datetime.strptime(H,O);N=N.replace(hour=23,minute=59,second=59,microsecond=999999,tzinfo=K);J['to']=int(N.timestamp())
		C.fetcher.validate(J);Q=C.fetcher.fetch(endpoint='/historical/prices/ohlcv',params=J);A=C.fetcher.to_dataframe(Q['data']);A[B]=pd.to_datetime(A[B])
		if A[B].dt.tz is _A:A[B]=A[B].dt.tz_localize(K)
		else:A[B]=A[B].dt.tz_convert(K)
		A[B]=A[B].dt.tz_localize(_A).dt.normalize();A.set_index(B,inplace=True)
		if P is not _A:A=A[P]
		if D is not _A and str(D).isdigit():A=A.tail(int(D)).copy()
		return A
	def _gold_vn_buy(A,start=_A,end=_A,length=_A):'Lấy giá vàng Việt Nam (mua vào).';return A._fetch_commodity('GOLD:VN:BUY',start,end,columns=[_C],length=length)
	def _gold_vn_sell(A,start=_A,end=_A,length=_A):'Lấy giá vàng Việt Nam (bán ra).';return A._fetch_commodity('GOLD:VN:SELL',start,end,columns=[_C],length=length)
	@agg_execution(_B)
	def gold_vn(self,start=_A,end=_A,length=_A):'Lấy giá vàng Việt Nam.';C=length;B=start;D=self._gold_vn_buy(B,end,length=C);E=self._gold_vn_sell(B,end,length=C);A=pd.concat([D,E],axis=1);A.columns=['buy','sell'];A=A.ffill();return A
	@agg_execution(_B)
	def gold_global(self,start=_A,end=_A,length=_A):'Lấy giá vàng thế giới.';return self._fetch_commodity('GC=F',start,end,length=length)
	@agg_execution(_B)
	def _gas_ron92(self,start=_A,end=_A,length=_A):'Lấy giá xăng RON92 tại Việt Nam.';return self._fetch_commodity('GAS:RON92:VN',start,end,columns=[_C],length=length)
	@agg_execution(_B)
	def _gas_ron95(self,start=_A,end=_A,length=_A):'Lấy giá xăng RON95 tại Việt Nam.';return self._fetch_commodity('GAS:RON95:VN',start,end,columns=[_C],length=length)
	@agg_execution(_B)
	def _oil_do(self,start=_A,end=_A,length=_A):'Lấy giá dầu DO tại Việt Nam.';return self._fetch_commodity('GAS:DO:VN',start,end,columns=[_C],length=length)
	@agg_execution(_B)
	def gas_vn(self,start=_A,end=_A,length=_A):'Lấy giá xăng và dầu DO tại Việt Nam.';E=length;D=end;C=start;B=self;F=B._gas_ron92(C,D,length=E);G=B._gas_ron95(C,D,length=E);H=B._oil_do(C,D,length=E);A=pd.concat([G,F,H],axis=1);A.columns=['ron95','ron92','oil_do'];A=A.ffill();return A
	@agg_execution(_B)
	def oil_crude(self,start=_A,end=_A,length=_A):'Lấy giá dầu thô.';return self._fetch_commodity('CL=F',start,end,length=length)
	@agg_execution(_B)
	def gas_natural(self,start=_A,end=_A,length=_A):'Lấy giá khí thiên nhiên.';return self._fetch_commodity('NG=F',start,end,length=length)
	@agg_execution(_B)
	def coke(self,start=_A,end=_A,length=_A):'Lấy giá than cốc.';return self._fetch_commodity('ICEEUR:NCF1!',start,end,length=length)
	@agg_execution(_B)
	def steel_d10(self,start=_A,end=_A,length=_A):'Lấy giá thép D10 tại Việt Nam.';return self._fetch_commodity('STEEL:D10:VN',start,end,columns=[_C],length=length)
	@agg_execution(_B)
	def iron_ore(self,start=_A,end=_A,length=_A):'Lấy giá quặng sắt.';return self._fetch_commodity('COMEX:TIO1!',start,end,length=length)
	@agg_execution(_B)
	def steel_hrc(self,start=_A,end=_A,length=_A):'Lấy giá thép HRC.';return self._fetch_commodity('COMEX:HRC1!',start,end,length=length)
	@agg_execution(_B)
	def fertilizer_ure(self,start=_A,end=_A,length=_A):'Lấy giá phân ure.';return self._fetch_commodity('CBOT:UME1!',start,end,length=length)
	@agg_execution(_B)
	def soybean(self,start=_A,end=_A,length=_A):'Lấy giá đậu tương.';return self._fetch_commodity('ZM=F',start,end,length=length)
	@agg_execution(_B)
	def corn(self,start=_A,end=_A,length=_A):'Lấy giá ngô (bắp).';return self._fetch_commodity('ZC=F',start,end,length=length)
	@agg_execution(_B)
	def sugar(self,start=_A,end=_A,length=_A):'Lấy giá đường.';return self._fetch_commodity('SB=F',start,end,length=length)
	@agg_execution(_B)
	def pork_north_vn(self,start=_A,end=_A,length=_A):'Lấy giá heo hơi miền Bắc Việt Nam.';return self._fetch_commodity('PIG:NORTH:VN',start,end,columns=[_C],length=length)
	@agg_execution(_B)
	def pork_china(self,start=_A,end=_A,length=_A):'Lấy giá heo hơi Trung Quốc.';return self._fetch_commodity('PIG:CHINA',start,end,columns=[_C],length=length)
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register(_D,'spl',CommodityPrice)