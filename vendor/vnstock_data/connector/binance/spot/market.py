_R='endTime'
_Q='startTime'
_P='Buy'
_O='Sell'
_N='raw'
_M='close_time'
_L='is_buyer_maker'
_K='qty'
_J='price'
_I='id'
_H='limit'
_G=True
_F='match_type'
_E='side'
_D='volume'
_C=None
_B='time'
_A='symbol'
import pandas as pd
from vnstock_data.connector.binance.spot._base import BinanceSpotBase
class SpotMarket:
	"\n    Binance Spot Market Data – Implementation Layer.\n\n    All public REST endpoints are exposed with **provider-agnostic names**\n    aligned with the Vnstock Unified UI naming convention (mirrors FIX / Bloomberg\n    terminology where applicable). The Unified UI facade delegates to these methods\n    via the registry.\n\n    Endpoint mapping (method → Binance REST endpoint):\n    ────────────────────────────────────────────────────\n    ohlcv           → GET /api/v3/uiKlines       (display-optimised candlesticks)\n    ohlcv_raw       → GET /api/v3/klines          (raw candlesticks, full fields)\n    trades          → GET /api/v3/trades           (mode='raw', default)\n                    → GET /api/v3/aggTrades        (mode='aggregate')\n    trade_history   → GET /api/v3/historicalTrades (older trades by ID)\n    order_book      → GET /api/v3/depth            (L2 Market Depth)\n    quote           → GET /api/v3/ticker/24hr      (24-h rolling quote snapshot)\n    vwap            → GET /api/v3/avgPrice         (Volume-Weighted Average Price)\n    daily_stats     → GET /api/v3/ticker/tradingDay(trading-day session stats)\n    last_price      → GET /api/v3/ticker/price     (last traded price)\n    rolling_stats   → GET /api/v3/ticker           (rolling-window statistics)\n    reference_price → GET /api/v3/referencePrice   (reference / indicative price)\n    reference_calc  → GET /api/v3/referencePrice/calculation\n\n    Connector-only (not exposed in Unified UI):\n    ────────────────────────────────────────────\n    bbo             → GET /api/v3/ticker/bookTicker(best bid / offer)\n    "
	def __init__(A,symbol):A.symbol=symbol
	def _format_columns(G,df):
		'Convert camelCase → snake_case, coerce timestamps & numerics.';D='timestamp';C='open_time';A=df
		if A.empty:return A
		E={A:''.join(['_'+A.lower()if A.isupper()else A for A in A]).lstrip('_')for A in A.columns};A.rename(columns=E,inplace=_G);A=A.loc[:,~A.columns.duplicated()].copy()
		for B in(_B,C,_M,D):
			if B in A.columns:A[B]=pd.to_datetime(A[B],unit='ms').dt.tz_localize(_C)
		F={_A,_E,_F,_I,_B,C,_M,D}
		for B in A.columns:
			if B not in F:A[B]=pd.to_numeric(A[B],errors='coerce')
		return A
	def ohlcv(D,interval='1d',start_time=_C,end_time=_C,limit=500,mode=_C,**N):
		"\n        Historical OHLCV candlestick bars.\n\n        Args:\n            interval (str): Timeframe – ``1s``, ``1m``–``30m``, ``1h``–``12h``,\n                ``1d``, ``3d``, ``1w``, ``1M``.\n            limit (int): Number of bars (default 500, max 1000).\n            mode (str | None):\n                - ``None`` (default) – chart-optimised UIKlines that filters\n                  anomalous data. Binance: ``GET /api/v3/uiKlines``.\n                - ``'raw'`` – full kline with extra fields (``quote_volume``,\n                  ``trades``, ``taker_buy_base_vol``, ``taker_buy_quote_vol``).\n                  Binance: ``GET /api/v3/klines``.\n        ";K='close';J='low';I='high';H='open';F=end_time;E=start_time;C='ignore';L=[_B,H,I,J,K,_D,_M,'quote_volume','trades','taker_buy_base_vol','taker_buy_quote_vol',C];B={_A:D.symbol.upper(),'interval':interval,_H:limit}
		if E:B[_Q]=E
		if F:B[_R]=F
		M='/api/v3/klines'if mode==_N else'/api/v3/uiKlines';G=BinanceSpotBase._request(M,B)
		if not G:return pd.DataFrame()
		A=pd.DataFrame(G,columns=L);A=D._format_columns(A)
		if mode==_N:return A.drop(columns=[C],errors=C)
		return A[[_B,H,I,J,K,_D]]
	def order_book(G,limit=10,**I):
		'\n        L2 order book depth – top N bid/ask price levels.\n\n        Binance endpoint: ``GET /api/v3/depth``\n        ';C=limit;H={_A:G.symbol.upper(),_H:C};D=BinanceSpotBase._request('/api/v3/depth',H)
		if not D:return pd.DataFrame()
		A={}
		for(B,E)in enumerate(D.get('bids',[])[:C]):A[f"bid_price_{B+1}"]=float(E[0]);A[f"bid_vol_{B+1}"]=float(E[1])
		for(B,F)in enumerate(D.get('asks',[])[:C]):A[f"ask_price_{B+1}"]=float(F[0]);A[f"ask_vol_{B+1}"]=float(F[1])
		return pd.DataFrame([A])
	def intraday(D,limit=500,mode=_N,start_time=_C,end_time=_C,**J):
		"\n        Tick-by-tick trade tape (Time & Sales).\n\n        Args:\n            limit (int): Number of records (default 500, max 1000).\n            mode (str):\n                - ``'raw'`` (default) – individual fills from ``GET /api/v3/trades``.\n                - ``'aggregate'`` – compressed fills aggregated at same price &\n                  direction, from ``GET /api/v3/aggTrades``.  Consecutive fills at\n                  the same price and side are merged into one record.\n            start_time (int): Unix ms – used only with ``mode='aggregate'``.\n            end_time (int): Unix ms – used only with ``mode='aggregate'``.\n\n        Returns:\n            pd.DataFrame: Schema ``[time, price, volume, side, match_type, id]``\n        ";G=end_time;F=start_time;E=limit
		if mode=='aggregate':
			B={_A:D.symbol.upper(),_H:E}
			if F:B[_Q]=F
			if G:B[_R]=G
			C=BinanceSpotBase._request('/api/v3/aggTrades',B)
			if not C:return pd.DataFrame()
			A=pd.DataFrame(C);H={'T':_B,'p':_J,'q':_D,'a':_I};A.rename(columns={B:C for(B,C)in H.items()if B in A.columns},inplace=_G);A=D._format_columns(A)
			if'm'in A.columns:A[_E]=A['m'].apply(lambda x:_O if x else _P)
			A[_F]='Aggregate'
		else:
			B={_A:D.symbol.upper(),_H:E};C=BinanceSpotBase._request('/api/v3/trades',B)
			if not C:return pd.DataFrame()
			A=pd.DataFrame(C)
			if _K in A.columns:A.rename(columns={_K:_D},inplace=_G)
			A=D._format_columns(A)
			if _L in A.columns:A[_E]=A[_L].apply(lambda x:_O if x else _P)
			A[_F]='Normal'
		I=[_B,_J,_D,_E,_F,_I];return A[[B for B in I if B in A.columns]]
	def trade_history(B,limit=500,from_id=_C,**G):
		'\n        Historical trade look-up (paginate by trade ID for older data).\n\n        Binance endpoint: ``GET /api/v3/historicalTrades``\n        ';C=from_id;D={_A:B.symbol.upper(),_H:limit}
		if C:D['fromId']=C
		E=BinanceSpotBase._request('/api/v3/historicalTrades',D)
		if not E:return pd.DataFrame()
		A=pd.DataFrame(E)
		if _K in A.columns:A.rename(columns={_K:_D},inplace=_G)
		A=B._format_columns(A)
		if _L in A.columns:A[_E]=A[_L].apply(lambda x:_O if x else _P)
		A[_F]='Historical';F=[_B,_J,_D,_E,_F,_I];return A[[B for B in F if B in A.columns]]
	def quote(A,**D):
		'\n        24-hour rolling price-change statistics (quote snapshot).\n\n        Binance endpoint: ``GET /api/v3/ticker/24hr``\n        ';C={_A:A.symbol.upper()};B=BinanceSpotBase._request('/api/v3/ticker/24hr',C)
		if not B:return pd.DataFrame()
		return A._format_columns(pd.DataFrame([B]))
	def vwap(A,**D):
		'\n        Volume-Weighted Average Price over the last N minutes.\n\n        Binance endpoint: ``GET /api/v3/avgPrice``\n        ';C={_A:A.symbol.upper()};B=BinanceSpotBase._request('/api/v3/avgPrice',C)
		if not B:return pd.DataFrame()
		return A._format_columns(pd.DataFrame([B]))
	def daily_stats(A,**D):
		'\n        Trading-day stats (open, high, low, close, volume for the current day).\n\n        Binance endpoint: ``GET /api/v3/ticker/tradingDay``\n        ';C={_A:A.symbol.upper()};B=BinanceSpotBase._request('/api/v3/ticker/tradingDay',C)
		if not B:return pd.DataFrame()
		return A._format_columns(pd.DataFrame([B]))
	def last_price(A,**D):
		'\n        Most-recent last traded price – ultra-lightweight single-field response.\n\n        Binance endpoint: ``GET /api/v3/ticker/price``\n        ';C={_A:A.symbol.upper()};B=BinanceSpotBase._request('/api/v3/ticker/price',C)
		if not B:return pd.DataFrame()
		return A._format_columns(pd.DataFrame([B]))
	def rolling_stats(B,window_size='1d',**E):
		'\n        Rolling-window price-change statistics over a custom window.\n\n        Binance endpoint: ``GET /api/v3/ticker``\n        ';C={_A:B.symbol.upper(),'windowSize':window_size};A=BinanceSpotBase._request('/api/v3/ticker',C)
		if not A:return pd.DataFrame()
		D=pd.DataFrame([A]if isinstance(A,dict)else A);return B._format_columns(D)
	def reference_price(A,mode=_J,**D):
		"\n        Reference (indicative) price for mark / liquidation calculations.\n\n        Args:\n            mode (str):\n                - ``'price'`` (default) – reference price only.\n                  Binance: ``GET /api/v3/referencePrice``.\n                - ``'calc'`` – detailed calculation breakdown.\n                  Binance: ``GET /api/v3/referencePrice/calculation``.\n\n        Note: Not all symbols have a reference price; returns empty DataFrame if unavailable.\n        ";C='/api/v3/referencePrice/calculation'if mode=='calc'else'/api/v3/referencePrice';B=BinanceSpotBase._request(C,{_A:A.symbol.upper()})
		if not B:return pd.DataFrame()
		return A._format_columns(pd.DataFrame([B]))
	def bbo(A,**E):
		'\n        Best Bid / Offer (top-of-book snapshot, single price level).\n\n        This is a connector-only method not exposed in the Unified UI facade,\n        because ``order_book(limit=1)`` provides equivalent information with a\n        richer schema.  Use this when you need the absolute minimalist payload.\n\n        Binance endpoint: ``GET /api/v3/ticker/bookTicker``\n        ';D={_A:A.symbol.upper()};B=BinanceSpotBase._request('/api/v3/ticker/bookTicker',D)
		if not B:return pd.DataFrame()
		C=pd.DataFrame([B]);C.rename(columns={'bidPrice':'bid_price_1','bidQty':'bid_vol_1','askPrice':'ask_price_1','askQty':'ask_vol_1'},inplace=_G);return A._format_columns(C)