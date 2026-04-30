'History module for ForexSB.'
_J=False
_I='4H'
_H='volume'
_G='30'
_F=True
_E='close'
_D='low'
_C='high'
_B='open'
_A='time'
import struct,gzip,datetime
from typing import Dict,Optional,Union
import pandas as pd,requests
from vnstock.core.utils.lookback import get_start_date_from_lookback
from vnai import agg_execution
from vnstock.core.models import TickerModel
from vnstock.core.utils.logger import get_logger
from vnstock.core.utils.interval import normalize_interval
from vnstock_data.core.utils.user_agent import get_headers
try:from vnstock.explorer.vci.const import _OHLC_MAP
except ImportError:_OHLC_MAP={_A:_A,_B:_B,_C:_C,_D:_D,_E:_E,_H:_H}
logger=get_logger(__name__)
_FXSB_INTERVAL_MAP={'1m':'1','5m':'5','15m':'15','30m':_G,'1H':_G,_I:_G,'1D':_G,'1W':_G}
class Quote:
	'\n    Cấu hình truy cập dữ liệu lịch sử giá cho các cặp ngoại tệ từ ForexSB.\n    '
	def __init__(A,symbol,random_agent=_J,show_log=_J,**C):
		B=show_log;A.symbol=symbol.upper();A.data_source='FXSB';A.base_url='https://data.forexsb.com/datafeed/data/dukascopy/';A.interval_map=_FXSB_INTERVAL_MAP;A.show_log=B
		if not B:logger.setLevel('CRITICAL')
	def _input_validation(B,start,end,interval):
		'\n        Validate input data format and interval.\n        ';C=interval
		try:
			if str(C).upper()in['H4',_I]:A=_I
			else:D=normalize_interval(C);A=D.value
		except ValueError:raise ValueError(f"Giá trị interval không hợp lệ: {C}.")
		if A not in B.interval_map:E=', '.join(B.interval_map.keys());raise ValueError(f"Giá trị interval không được FXSB hỗ trợ: {A}. Hỗ trợ cơ bản và mở rộng: {E}")
		F=TickerModel(symbol=B.symbol,start=start,end=end,interval=A);return F
	@agg_execution('FXSB.ext')
	def history(self,start='',end='',interval='1D',to_df=_F,show_log=_J,length=100000,floating=5):
		'\n        Tải dữ liệu OHLC từ file .lb.gz của ForexSB.\n\n        Tham số:\n            - start (tùy chọn): thời gian bắt đầu lấy dữ liệu (YYYY-MM-DD). \n            - end (tùy chọn): thời gian kết thúc lấy dữ liệu.\n            - interval (tùy chọn): Khung thời gian.\n            - to_df (tùy chọn): Chuyển đổi về DataFrame.\n            - count_back (tùy chọn): Giới hạn số bars cuối cùng. Mặc định là 100,000 để an toàn,\n                                     có thể lấy toàn bộ file nếu cần.\n            - length (tùy chọn): khoảng thời gian quy ước.\n        ';O='left';N='extra';M=floating;J=None;E=end;D=start;C=self;B=length
		if not E:E=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
		if not D:
			if B:
				G=str(B).lower()
				if G.endswith('b'):B=int(G[:-1])
				elif G.isdigit():B=int(G)
				else:D=get_start_date_from_lookback(lookback_length=str(B).upper(),end_date=E)
			else:B=100000
		H=C._input_validation(D if D else'1970-01-01',E,interval);P=C.interval_map[H.interval];I=f"{C.base_url}{C.symbol}{P}.lb.gz"
		try:F=requests.get(I,headers=get_headers('FXSB',random_agent=_J,browser='chrome',platform='macos'),timeout=15)
		except requests.exceptions.Timeout:raise ConnectionError(f"ForexSB request timed out sau 15 giây cho symbol {C.symbol} (interval={H.interval}). Kiểm tra kết nối mạng hoặc thử lại sau. URL: {I}")
		except requests.exceptions.RequestException as K:raise ConnectionError(f"ForexSB connection error: {K}. URL: {I}")
		if F.status_code!=200:raise ValueError(f"Không thể truy xuất dữ liệu từ ForexSB cho symbol {C.symbol} (Status {F.status_code}). URL: {I}")
		try:
			if F.content[:2]==b'\x1f\x8b':L=gzip.decompress(F.content)
			else:L=F.content
		except Exception as K:raise ValueError(f"Lỗi khi giải nén dữ liệu: {K}")
		W=[];Q=28;X=len(L)//Q;R=struct.iter_unpack('<IIIIIII',L);S=[_A,_B,_C,_D,_E,_H,N];A=pd.DataFrame(R,columns=S);A[_A]=pd.to_datetime(A[_A],unit='m',origin='2000-01-01',utc=_F);A[_A]=A[_A].dt.tz_localize(J);A[_B]=A[_B]/100000;A[_C]=A[_C]/100000;A[_D]=A[_D]/100000;A[_E]=A[_E]/100000;A=A.drop(columns=[N])
		if H.interval in['1H',_I,'1D','1W']:A.set_index(_A,inplace=_F);T=H.interval.replace('H','h').replace('D','D').replace('W','W');A=A.resample(T,label=O,closed=O).agg({_B:'first',_C:'max',_D:'min',_E:'last',_H:'sum'}).dropna().reset_index()
		if D is not J and D!='':U=pd.to_datetime(D);A=A[A[_A]>=U]
		if E is not J and E!='':V=pd.to_datetime(E)+pd.Timedelta(days=1);A=A[A[_A]<V]
		A=A.reset_index(drop=_F)
		if B and isinstance(B,int)and B>0:A=A.tail(B).reset_index(drop=_F)
		elif A.shape[0]>100000:A=A.tail(100000).reset_index(drop=_F)
		if M is not J:A=A.round(M)
		A.source=C.data_source
		if to_df:return A
		else:return A.to_json(orient='records')
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('quote','fxsb',Quote)