'Trading module for KB Securities (KBS) data source.'
_q='symbols'
_p='reference_price'
_o='category'
_n='total_volume'
_m='floor_price'
_l='ceiling_price'
_k='total_sell_trade_volume'
_j='total_sell_trade'
_i='total_buy_trade_volume'
_h='total_buy_trade'
_g='average_price'
_f='stock'
_e='price_change'
_d='data'
_c=True
_b='vi'
_a='same-origin'
_Z='cors'
_Y='empty'
_X='application/json'
_W='keep-alive'
_V='en-US,en;q=0.9,vi;q=0.8'
_U='x-lang'
_T='Sec-Fetch-Site'
_S='Sec-Fetch-Mode'
_R='Sec-Fetch-Dest'
_Q='DNT'
_P='Content-Type'
_O='Connection'
_N='Accept-Language'
_M='matched_volume'
_L='GET'
_K='code'
_J='trading_date'
_I='HOSE'
_H='exchange'
_G='source'
_F='KBS.ext'
_E='coerce'
_D='timestamp'
_C=None
_B=False
_A='symbol'
import pandas as pd,json,re
from datetime import datetime
from typing import Optional,List
from vnai import agg_execution
from vnstock.core.utils.logger import get_logger
from vnstock.core.utils.parser import get_asset_type,camel_to_snake
from vnstock.core.utils.client import send_request,ProxyConfig
from vnstock_data.core.utils.user_agent import get_headers
from vnstock_data.explorer.kbs.const import _IIS_BASE_URL,_STOCK_TRADE_HISTORY_URL,_PUT_THROUGH_HISTORY_URL,_STOCK_MATCHED_BY_PRICE_URL,_STOCK_ISS_URL,_ODD_LOT_ISS_URL,_PUT_THROUGH_ISS_URL,_DERIVATIVE_ISS_URL,_PRICE_BOARD_MAP,_ODD_LOT_MAP,_TRADE_HISTORY_MAP,_PUT_THROUGH_MAP,_MATCHED_BY_PRICE_MAP,_DERIVATIVE_MAP,_INDEX_SUMMARY_URL,_INDEX_SUMMARY_MAP,_INDEX_SYMBOL_TO_CODE,_PRICE_BOARD_STANDARD_COLUMNS,_PUT_THROUGH_STANDARD_COLUMNS,_DERIVATIVE_STANDARD_COLUMNS,_KBS_TO_SCHEMA_MAP,_EXCLUDED_COLUMNS,_EXCHANGE_CODE_MAP
logger=get_logger(__name__)
class Trading:
	'\n    Lớp truy cập dữ liệu giao dịch từ KB Securities (KBS).\n    '
	def __init__(A,symbol=_C,random_agent=_B,proxy_config=_C,show_log=_B,proxy_mode=_C,proxy_list=_C):
		"\n        Khởi tạo Trading client cho KBS.\n\n        Args:\n            symbol: Mã chứng khoán (VD: 'ACB', 'VNM'). Optional cho market-wide queries.\n            random_agent: Sử dụng user agent ngẫu nhiên. Mặc định False.\n            proxy_config: Cấu hình proxy. Mặc định None.\n            show_log: Hiển thị log debug. Mặc định False.\n            proxy_mode: Chế độ proxy (try, rotate, random, single). Mặc định None.\n            proxy_list: Danh sách proxy URLs. Mặc định None.\n        ";F=proxy_mode;E=show_log;D=proxy_config;C=proxy_list;B=symbol
		if isinstance(B,list):A.symbol=[A.upper()for A in B]
		else:A.symbol=B.upper()if B else _C
		A.data_source='KBS';A.base_url=_IIS_BASE_URL;A.headers=get_headers(data_source=A.data_source,random_agent=random_agent);A.show_log=E
		if D is _C:
			H=F if F else'try';G='direct'
			if C and len(C)>0:G='proxy'
			A.proxy_config=ProxyConfig(proxy_mode=H,proxy_list=C,request_mode=G)
		else:A.proxy_config=D
		if A.symbol:
			if isinstance(A.symbol,str):A.asset_type=get_asset_type(A.symbol)
			else:A.asset_type=_C
		if not E:logger.setLevel('CRITICAL')
	@agg_execution(_F)
	def price_history(self,start=_C,end=_C,limit=1000,page=1,show_log=_B):
		'\n        Truy xuất dữ liệu lịch sử giá kết hợp giao dịch khớp lệnh/thoả thuận (OHLCV + Stats)\n        Hàm này mô phỏng sát nhất với cấu trúc price_history truyền thống của VCI.\n        \n        Args:\n            start: Ngày bắt đầu (YYYY-MM-DD).\n            end: Ngày kết thúc (YYYY-MM-DD).\n            limit: Số bản ghi trả về tối đa.\n            page: Phân trang (offset/page index).\n            \n        Returns:\n            DataFrame dữ liệu lịch sử.\n        ';G=start;F='deal_value';E='deal_volume';D='matched_value';B=self
		if not B.symbol:raise ValueError('Symbol is required for price_history method.')
		I=f"{_IIS_BASE_URL}/{B.symbol}/historical-quotes";C={'limit':limit,'offset':page}
		if G and end:C['startDate']=G;C['endDate']=end
		H=send_request(url=I,headers=B.headers,method=_L,params=C,show_log=show_log or B.show_log,proxy_list=B.proxy_config.proxy_list,proxy_mode=B.proxy_config.proxy_mode,request_mode=B.proxy_config.request_mode)
		if not H:return pd.DataFrame()
		A=pd.DataFrame(H)
		if A.empty:return A
		J={'TradingDate':_J,'StockCode':_A,'Change':_e,'PerChange':'percent_price_change','ClosePrice':'close','MT_TotalVol':_M,'MT_TotalVal':D,'PT_TotalVol':E,'PT_TotalVal':F,'AvrPrice':_g,'HighestPrice':'high','LowestPrice':'low','TotalBuyTrade':_h,'TotalBuyVol':_i,'TotalSellTrade':_j,'TotalSellVol':_k,'CeilingPrice':_l,'FloorPrice':_m};A=A.rename(columns=J)
		if _J in A.columns:A[_J]=pd.to_datetime(A[_J],format='%d/%m/%Y',errors=_E)
		if _M in A.columns and E in A.columns:A[_n]=A[_M]+A[E]
		if D in A.columns and F in A.columns:A['total_value']=A[D]+A[F]
		if _A in A.columns:A=A.drop(columns=[_A])
		A.attrs[_A]=B.symbol;A.attrs[_G]=B.data_source;return A
	@agg_execution(_F)
	def order_stats(self,start=_C,end=_C,limit=1000,page=1,show_log=_B):
		'\n        Khởi tạo alias cho thống kê cung cầu (Order Statistics).\n        Vì KBS đã trả về thông tin Tổng Lượng Mua/Bán trong dữ liệu Historical Quotes,\n        ta uỷ quyền qua price_history.\n        ';A=self.price_history(start=start,end=end,limit=limit,page=page,show_log=show_log)
		if A.empty:return A
		B=[_J,'close',_g,_e,_M,_i,_k,_h,_j];C=[B for B in B if B in A.columns];A=A[C];A.attrs[_o]='order_stats';A.attrs[_A]=self.symbol;return A
	@agg_execution(_F)
	def foreign_trade(self,top=10,show_log=_B):
		'\n        Lấy top Giao dịch của nhà đầu tư nước ngoài (Realtime Ranking).\n        API này trả về top các mã dựa trên ranking chứ không truy xuất theo từng mã (KBS không cấp).\n        Do đó nếu self.symbol đã gán, API này sẽ lờ đi và dùng `top`.\n        ';A=self;D=f"{_IIS_BASE_URL}/rtranking/foreignTotal";E={'top':top};C=send_request(url=D,headers=A.headers,method=_L,params=E,show_log=show_log or A.show_log,proxy_list=A.proxy_config.proxy_list,proxy_mode=A.proxy_config.proxy_mode,request_mode=A.proxy_config.request_mode)
		if not C:return pd.DataFrame()
		B=pd.DataFrame(C);F={'SB':_A,'EX':_H,'RE':_p,'CL':_l,'FL':_m,'CP':'match_price','FB':'foreign_buy_volume','FS':'foreign_sell_volume','FT':'foreign_total_volume'};B=B.rename(columns=F);B.attrs[_o]='foreign_trade';B.attrs[_G]=A.data_source;return B
	@agg_execution(_F)
	def matched_by_price(self,show_log=_B):
		"\n        Truy xuất dữ liệu khớp lệnh theo từng mức giá.\n\n        Args:\n            show_log: Hiển thị log debug.\n\n        Returns:\n            DataFrame chứa dữ liệu khớp lệnh theo giá với các cột chuẩn hóa.\n\n        Examples:\n            >>> trading = Trading('ACB')\n            >>> df = trading.matched_by_price()\n\n        Raises:\n            ValueError: Nếu không có symbol được chỉ định.\n        ";C=show_log;A=self
		if not A.symbol:raise ValueError('Symbol is required for matched_by_price method.')
		E=f"{_STOCK_MATCHED_BY_PRICE_URL}/{A.symbol}";D=send_request(url=E,headers=A.headers,method=_L,show_log=C or A.show_log,proxy_list=A.proxy_config.proxy_list,proxy_mode=A.proxy_config.proxy_mode,request_mode=A.proxy_config.request_mode)
		if not D:return pd.DataFrame()
		B=pd.DataFrame(D);B=B.rename(columns=_MATCHED_BY_PRICE_MAP);B.attrs[_A]=A.symbol;B.attrs[_G]=A.data_source
		if C or A.show_log:logger.info(f"Truy xuất thành công dữ liệu khớp lệnh theo giá cho {A.symbol}.")
		return B
	@agg_execution(_F)
	def index_summary(self,show_log=_B):
		'\n        Truy xuất thông tin tóm tắt (Snapshot) cho các chỉ số thị trường.\n\n        Chấp nhận mã symbol (VNINDEX, VN30, ...) và tự động mapping sang mã KBS (HOSE, 30, ...).\n        Nếu không có symbol, mặc định lấy toàn bộ các chỉ số chính.\n\n        Args:\n            show_log: Hiển thị log debug.\n\n        Returns:\n            DataFrame chứa thông tin tóm tắt chỉ số với các cột chuẩn hóa.\n        ';F=show_log;B=self;import requests as J;K=_INDEX_SUMMARY_URL
		if B.symbol:
			E=_INDEX_SYMBOL_TO_CODE.get(B.symbol)
			if not E:E=B.symbol
			G={_K:E}
		else:G={_K:'HOSE,30,100,HNX,HNX30,UPCOM'}
		try:
			H=B.headers.copy();H.update({_N:_V,_O:_W,_P:_X,_Q:'1',_R:_Y,_S:_Z,_T:_a,_U:_b});I=J.post(K,headers=H,data=json.dumps(G),timeout=30)
			if I.status_code in[200,201]:D=I.json()
			else:return pd.DataFrame()
		except Exception as L:
			if F or B.show_log:logger.error(f"Failed to fetch index summary data: {str(L)}")
			return pd.DataFrame()
		if not D or not isinstance(D,list):return pd.DataFrame()
		A=pd.DataFrame(D);A=A.rename(columns=_INDEX_SUMMARY_MAP);M={B:A for(A,B)in _INDEX_SYMBOL_TO_CODE.items()}
		if'MC'in D[0]:A[_A]=A['MC'].map(lambda x:M.get(str(x),x))
		N=['close_price',_e,'open_price','high_price','low_price',_p,'previous_close']
		for C in N:
			if C in A.columns:A[C]=pd.to_numeric(A[C],errors=_E)
		O=['accumulated_volume','accumulated_value',_n,'put_through_value','put_through_volume','advances','declines','no_change']
		for C in O:
			if C in A.columns:A[C]=pd.to_numeric(A[C],errors=_E)
		if _D in A.columns:A[_D]=pd.to_datetime(A[_D],unit='ms',errors=_E)
		A.attrs[_G]=B.data_source
		if B.symbol:A.attrs[_A]=B.symbol
		if F or B.show_log:logger.info(f"Truy xuất thành công tóm tắt cho {len(A)} chỉ số.")
		return A
	def _fetch_stock_board(D,symbols_list,show_log=_B):
		'\n        Fetch stock board (lô chẵn) data from /stock/iss endpoint.\n        \n        Args:\n            symbols_list: List of stock symbols.\n            show_log: Show debug logs.\n            \n        Returns:\n            DataFrame with stock board data.\n        ';B=symbols_list;import requests as G
		if isinstance(B,str):B=[B]
		H=_STOCK_ISS_URL;I={_K:','.join(B)}
		try:
			E=D.headers.copy();E.update({_N:_V,_O:_W,_P:_X,_Q:'1',_R:_Y,_S:_Z,_T:_a,_U:_b});F=G.post(H,headers=E,data=json.dumps(I),timeout=30)
			if F.status_code in[200,201]:C=F.json()
			else:return pd.DataFrame()
		except Exception as J:
			if show_log or D.show_log:logger.error(f"Failed to fetch stock board data: {str(J)}")
			return pd.DataFrame()
		if not C or not isinstance(C,list):return pd.DataFrame()
		A=pd.DataFrame(C);A=A.rename(columns=_PRICE_BOARD_MAP)
		if _D in A.columns:A[_D]=pd.to_datetime(A[_D],unit='ms',errors=_E)
		return A
	def _fetch_put_through_board(C,symbols_list,show_log=_B):
		"\n        Fetch put-through board (thỏa thuận) data.\n        \n        Note: The put-through ISS endpoint doesn't exist. Use put_through() method instead\n        which fetches from /put-through/trade/history endpoint and returns all put-through data.\n        \n        Args:\n            symbols_list: List of stock symbols.\n            show_log: Show debug logs.\n            \n        Returns:\n            DataFrame with put-through board data filtered by symbols.\n        ";B=symbols_list;A=C.put_through(exchange=_I,page=1,show_log=show_log)
		if isinstance(B,str):B=[B]
		A=A.loc[:,~A.columns.duplicated(keep='first')]
		if _A in A.columns and len(A)>0:A=A[A[_A].isin(B)].reset_index(drop=_c)
		return A
	def _fetch_derivative_board(E,symbols_list,show_log=_B):
		'\n        Fetch derivative board data.\n        \n        Args:\n            symbols_list: List of derivative symbols.\n            show_log: Show debug logs.\n            \n        Returns:\n            DataFrame with derivative board data.\n        ';D='time';C=symbols_list;import requests as H
		if isinstance(C,str):C=[C]
		I=_DERIVATIVE_ISS_URL;J={_K:','.join(C)}
		try:
			F=E.headers.copy();F.update({_N:_V,_O:_W,_P:_X,_Q:'1',_R:_Y,_S:_Z,_T:_a,_U:_b});G=H.post(I,headers=F,data=json.dumps(J),timeout=30)
			if G.status_code in[200,201]:A=G.json()
			else:return pd.DataFrame()
		except Exception as K:
			if show_log or E.show_log:logger.error(f"Failed to fetch derivative board data: {str(K)}")
			return pd.DataFrame()
		if not A:return pd.DataFrame()
		if isinstance(A,dict)and _d in A:A=A[_d]
		if not isinstance(A,list):return pd.DataFrame()
		B=pd.DataFrame(A);B=B.rename(columns=_DERIVATIVE_MAP)
		if D in B.columns:B[D]=pd.to_datetime(B[D],unit='ms',errors=_E)
		return B
	@agg_execution(_F)
	def price_board(self,symbols_list,board=_f,exchange=_I,show_log=_B,get_all=_B):
		"\n        Fetch real-time price board for a list of symbols.\n\n        Unified interface for fetching price data from various board types:\n        - stock: Standard board (even lots)\n        - odd_lot: Odd-lot trades\n        - put_through: Negotiated/Put-through trades\n        - derivatives: Index futures\n\n        Args:\n            symbols_list (List[str]): List of symbols (e.g., ['ACB', 'VNM']).\n            board (str): Board type ('stock', 'odd_lot', 'put_through', 'derivatives').\n            exchange (str): Exchange ('HOSE', 'HNX', 'UPCOM').\n            show_log (bool): Display debug logs.\n            get_all (bool): If True, return all raw columns. Otherwise, standard columns.\n        ";W='phái sinh';V='derivatives';U='odd_lot';R=get_all;H=board;E=show_log;C=self;B=symbols_list
		if not B:raise ValueError('symbols_list không được để trống.')
		if isinstance(B,str):B=[B]
		S=[_f,U,'put_through',V]
		if H not in S:raise ValueError(f"board không hợp lệ. Các giá trị hợp lệ: {S}")
		B=[A.upper()for A in B];F=[]
		if H==_f:
			from vnstock.core.utils.parser import get_asset_type as X;from vnstock_data.core.utils.parser import safe_convert_derivative_symbol as N;I=[];J=[];K=[]
			for L in B:
				T=X(L)
				if T=='derivative':J.append(L)
				elif T=='index':K.append(L)
				else:I.append(L)
			if I:Y=C._fetch_stock_board(I,E);F.append((Y,_PRICE_BOARD_STANDARD_COLUMNS))
			if J:O=[N(A)for A in J];P=C._fetch_derivative_board(O,E);F.append((P,_DERIVATIVE_STANDARD_COLUMNS))
			if K:
				D=C.index_summary(show_log=E)
				if not D.empty and _A in D.columns:Z=[A.upper()for A in K];D=D[D[_A].isin(Z)].reset_index(drop=_c)
				if not D.empty:F.append((D,list(D.columns)))
			G=[]
			if I:G.append('cơ sở')
			if J:G.append(W)
			if K:G.append('chỉ số')
			M='hỗn hợp ('+' & '.join(G)+')'if len(G)>1 else G[0]if G else'lô chẵn'
		elif H==U:a=C.odd_lot(symbols_list=B,exchange=exchange,show_log=E);F.append((a,_PRICE_BOARD_STANDARD_COLUMNS));M='lô lẻ'
		elif H==V:from vnstock_data.core.utils.parser import safe_convert_derivative_symbol as N;O=[N(A)for A in B];P=C._fetch_derivative_board(O,E);F.append((P,_DERIVATIVE_STANDARD_COLUMNS));M=W
		else:b=C._fetch_put_through_board(B,E);F.append((b,_PUT_THROUGH_STANDARD_COLUMNS));M='thỏa thuận'
		Q=[]
		for(A,c)in F:
			if len(A)>0:
				if not R:d=[B for B in c if B in A.columns];A=A[d]
				else:e=[A for A in A.columns if A not in _EXCLUDED_COLUMNS];A=A[e]
				Q.append(A)
		if Q:
			A=pd.concat(Q,ignore_index=_c)
			if _H in A.columns:A[_H]=A[_H].map(lambda x:_EXCHANGE_CODE_MAP.get(x,x)if pd.notna(x)else x)
		else:A=pd.DataFrame()
		A.attrs[_q]=B;A.attrs['board']=H;A.attrs[_G]=C.data_source;A.attrs['get_all']=R
		if E or C.show_log:logger.info(f"Truy xuất thành công bảng giá {M} cho {len(B)} mã chứng khoán.")
		return A
	@agg_execution(_F)
	def odd_lot(self,symbols_list=_C,exchange=_I,show_log=_B):
		"\n        Truy xuất dữ liệu giao dịch lô lẻ (odd-lot) cho danh sách mã chứng khoán.\n\n        Note: Phương thức này là alias cho price_board() với data_type='odd_lot'.\n        Khuyến nghị sử dụng price_board(symbols_list, data_type='odd_lot') thay vì phương thức này.\n\n        Args:\n            symbols_list: Danh sách mã chứng khoán. Nếu None, truy xuất toàn bộ sàn.\n            exchange: Sàn giao dịch ('HOSE', 'HNX', 'UPCOM'). Mặc định 'HOSE'.\n            show_log: Hiển thị log debug.\n\n        Returns:\n            DataFrame chứa dữ liệu giao dịch lô lẻ với các cột chuẩn hóa.\n\n        Examples:\n            >>> trading = Trading()\n            >>> df = trading.odd_lot(symbols_list=['AAA', 'AAM'])\n            >>> df_all = trading.odd_lot(exchange='HOSE')\n\n        Raises:\n            ValueError: Nếu exchange không hợp lệ.\n        ";F=show_log;D=exchange;C=self;A=symbols_list;G=[_I,'HNX','UPCOM']
		if D not in G:raise ValueError(f"Exchange không hợp lệ. Các giá trị hợp lệ: {G}")
		K=f"{_IIS_BASE_URL}/odd-lot/iss"
		if A:
			if isinstance(A,str):A=[A]
			A=[A.upper()for A in A];H={_K:','.join(A)}
		else:H={_H:D}
		import requests as L
		try:
			I=C.headers.copy();I.update({_N:_V,_O:_W,_P:_X,_Q:'1',_R:_Y,_S:_Z,_T:_a,_U:_b});J=L.post(K,headers=I,data=json.dumps(H),timeout=30)
			if J.status_code in[200,201]:E=J.json()
			else:return pd.DataFrame()
		except Exception as M:
			if F or C.show_log:logger.error(f"Failed to fetch odd_lot data: {str(M)}")
			return pd.DataFrame()
		if not E:return pd.DataFrame()
		if not isinstance(E,list):return pd.DataFrame()
		B=pd.DataFrame(E);B=B.rename(columns=_ODD_LOT_MAP)
		if _D in B.columns:B[_D]=pd.to_datetime(B[_D],errors=_E)
		if A:B.attrs[_q]=A
		B.attrs[_H]=D;B.attrs[_G]=C.data_source
		if F or C.show_log:
			if A:logger.info(f"Truy xuất thành công {len(B)} bản ghi giao dịch lô lẻ cho {len(A)} mã chứng khoán.")
			else:logger.info(f"Truy xuất thành công {len(B)} bản ghi giao dịch lô lẻ cho sàn {D}.")
		return B
	@agg_execution(_F)
	def put_through(self,exchange=_I,symbol=_C,page=1,page_size=1000,show_log=_B):
		"\n        Truy xuất dữ liệu giao dịch thỏa thuận (put-through) theo sàn.\n\n        Args:\n            exchange: Sàn giao dịch ('HOSE', 'HNX', 'UPCOM'). Mặc định 'HOSE'.\n            symbol: Mã chứng khoán để lọc (VD: 'ACB'). Nếu None, lấy toàn bộ sàn.\n            page: Số trang. Mặc định 1.\n            page_size: Số lượng bản ghi mỗi trang. Mặc định 1000.\n            show_log: Hiển thị log debug.\n\n        Returns:\n            DataFrame chứa dữ liệu giao dịch thỏa thuận với các cột chuẩn hóa.\n\n        Examples:\n            >>> trading = Trading()\n            >>> df = trading.put_through(exchange='HOSE', page=1)\n\n        Raises:\n            ValueError: Nếu exchange không hợp lệ.\n        ";H='page';E=show_log;D=exchange;B=self;F=[_I,'HNX','UPCOM']
		if D not in F:raise ValueError(f"Exchange không hợp lệ. Các giá trị hợp lệ: {F}")
		I=f"{_PUT_THROUGH_HISTORY_URL}/{D}";J={H:page,'pageSize':page_size};C=send_request(url=I,headers=B.headers,method=_L,params=J,show_log=E or B.show_log,proxy_list=B.proxy_config.proxy_list,proxy_mode=B.proxy_config.proxy_mode,request_mode=B.proxy_config.request_mode)
		if not C:return pd.DataFrame()
		if isinstance(C,dict)and _d in C:C=C[_d]
		if not C or not isinstance(C,list):return pd.DataFrame()
		A=pd.DataFrame(C);A=A.rename(columns=_PUT_THROUGH_MAP);A=A.loc[:,~A.columns.duplicated()]
		if _D in A.columns:A[_D]=pd.to_datetime(A[_D],errors=_E)
		G=symbol or B.symbol
		if G and _A in A.columns:A=A[A[_A]==G.upper()].reset_index(drop=_c)
		A.attrs[_H]=D;A.attrs[_G]=B.data_source;A.attrs[H]=page
		if E or B.show_log:logger.info(f"Truy xuất thành công {len(A)} bản ghi giao dịch thỏa thuận cho sàn {D}.")
		return A
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('trading','kbs',Trading)