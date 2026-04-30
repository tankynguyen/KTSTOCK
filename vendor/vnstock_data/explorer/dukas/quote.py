"\nDukascopy Provider – OHLCV & Tick data module.\n\nMarket data from the Dukascopy Historical Data feed (jetta.dukas.com).\n\nAvailable REST endpoints:\n    GET /v1/candles/minute/{symbol}/{side}/{year}/{month}/{day}\n        → Minute candles for one calendar day.\n    GET /v1/candles/day/{symbol}/{side}\n        → Full daily candle history (no date parameter).\n    GET /v1/ticks/{symbol}/{year}/{month}/{day}/{hour}\n        → Tick data for one hour.\n\nAll other timeframes (1h, 4h, 1w, 1M) are computed by resampling:\n    1h / 4h  → fetch 1m data per day, resample\n    1w / 1M  → fetch full daily history, resample\n\nAPI Response Format\n───────────────────\nDukascopy returns **delta-encoded** compressed arrays:\n  - ``timestamp``  – Unix ms of the first bar's open time.\n  - ``shift``      – Bar duration in ms.\n  - ``multiplier`` – Price precision (e.g. 0.001 means integers represent 0.001 units).\n  - ``times``      – Cumulative time-step deltas (int); absolute = timestamp + cumsum(times)*shift\n  - ``opens/highs/lows/closes`` – Cumulative price deltas; absolute = open + cumsum(deltas)*multiplier\n  - ``volumes``    – Raw (non-delta) volume values.\n"
from __future__ import annotations
_U='Dukascopy.ext'
_T='records'
_S='volume'
_R='multiplier'
_Q='timestamp'
_P='bid'
_O='close'
_N='low'
_M='high'
_L='open'
_K='times'
_J='Asia/Ho_Chi_Minh'
_I='day'
_H=False
_G='minute'
_F='1m'
_E=True
_D='4h'
_C='1h'
_B=None
_A='time'
import datetime
from typing import Optional,Union
from itertools import accumulate
import pandas as pd,requests
from vnstock.core.utils.logger import get_logger
from vnai import agg_execution
logger=get_logger(__name__)
from vnstock_data.core.utils.user_agent import get_headers
from vnstock_data.explorer.dukas.const import _BASE_URL,_COMMON_SYMBOL_MAP,_SYMBOL_SUFFIX_PATTERN
def _clean_symbol(symbol):'Normalise a Dukascopy symbol code.\n\n    Accepts both the verbose instrument code (e.g. ``USA500.IDX-USD``) and the\n    short user-facing form (e.g. ``USA500``).  Both are converted to the exact\n    code expected by the API.\n\n    Currently a no-op transformation – the API accepts the full code directly.\n    The helper exists as a central place to add further normalization if needed.\n    ';import re;return re.sub(_SYMBOL_SUFFIX_PATTERN,'',symbol.strip().upper())
_INTERVAL_FETCH={_F:(_G,_B),_C:(_G,_C),_D:(_G,_D),'1d':(_I,_B),'1w':(_I,'1W'),'1M':(_I,'1MS')}
_MINUTE_BASED={_F,_C,_D}
def _session():A=requests.Session();A.headers.update(get_headers('DUKASCOPY',random_agent=_H,browser='chrome',platform='macos'));A.headers['accept']='application/json, text/plain, */*';return A
def _decode_candles(data,tz=_J):
	'Decode Dukascopy delta-compressed candle response into a DataFrame.';A=data;F=A[_Q];B=A[_R];G=A['shift'];D=list(accumulate(A[_K]));H=list(accumulate(A['opens']));I=list(accumulate(A['highs']));J=list(accumulate(A['lows']));K=list(accumulate(A['closes']));E=A.get('volumes',[0]*len(D));L=[{_A:pd.Timestamp(F+D[A]*G,unit='ms'),_L:H[A]*B,_M:I[A]*B,_N:J[A]*B,_O:K[A]*B,_S:E[A]if A<len(E)else 0}for A in range(len(D))];C=pd.DataFrame(L)
	if not C.empty:C[_A]=C[_A].dt.tz_localize('UTC').dt.tz_convert(tz).dt.tz_localize(_B)
	return C
def _decode_ticks(data,tz=_J):
	'Decode Dukascopy delta-compressed tick response into a DataFrame.';G='ask';A=data;H=A[_Q];C=A[_R];D=list(accumulate(A[_K]));I=list(accumulate(A['asks']));J=list(accumulate(A['bids']));E=A.get('askVolumes',[]);F=A.get('bidVolumes',[]);K=[{_A:pd.Timestamp(H+D[A],unit='ms'),G:I[A]*C,_P:J[A]*C,'ask_volume':E[A]if A<len(E)else 0,'bid_volume':F[A]if A<len(F)else 0}for A in range(len(D))];B=pd.DataFrame(K)
	if not B.empty:B[_A]=B[_A].dt.tz_localize('UTC').dt.tz_convert(tz).dt.tz_localize(_B);B['price']=round((B[G]+B[_P])/2,6)
	return B
def _safe_get(session,url):
	'GET with timeout. Returns None on 404 or empty data (no bars for that period).';B=url
	try:A=session.get(B,timeout=15)
	except requests.exceptions.Timeout:raise ConnectionError(f"Dukascopy timed out (15s): {B}")
	except requests.exceptions.RequestException as D:raise ConnectionError(f"Dukascopy connection error: {D}")
	if A.status_code==404:return
	if A.status_code!=200:raise ValueError(f"Dukascopy HTTP {A.status_code}: {B}")
	try:C=A.json()
	except Exception:return
	return C if C and C.get(_K)else _B
class Quote:
	"\n    Dukascopy market data – OHLCV (candles) and tick data.\n\n    Supports Forex, Commodities, Global Indices, Stocks, and Crypto.\n\n    Symbol format (use the ``code`` field from Dukascopy instruments list):\n        FX:     ``EUR-USD``, ``USD-JPY``, ``GBP-USD``\n        IDX:    ``USA500.IDX-USD``, ``GER30.IDX-EUR``, ``JPN225.IDX-JPY``\n        CMD:    ``COFFEE.CMD-USX``, ``OIL.CMD-USD``, ``WHEAT.CMD-USX``\n        STK:    ``AAPL.NYSE-USD``, ``AMZN.NSD-USD``\n        CRYPTO: ``BTCUSD``, ``ETHUSD``\n\n    Supported intervals: ``1m``, ``1h``, ``4h``, ``1d``, ``1w``, ``1M``\n\n    Side options:\n        ``'bid'`` (default), ``'ask'``, ``'mid'`` (average of bid + ask)\n\n    Note:\n        ``1h``, ``4h``, ``1w``, ``1M`` are computed by resampling lower-frequency data.\n    "
	def __init__(B,symbol,show_log=_H,**H):
		G='[^A-Z0-9]';F=show_log;E='code';B.timezone=H.get('timezone',_J);A=symbol.strip().upper()
		if A in _COMMON_SYMBOL_MAP:B.symbol=_COMMON_SYMBOL_MAP[A]
		else:
			try:
				from vnstock_data.explorer.dukas.listing import Listing as I;D=I(show_log=_H).all_symbols(to_df=_H);C=next((B for B in D if B[E].upper()==A),_B)
				if not C:C=next((B for B in D if B['symbol'].upper()==A),_B)
				if not C:import re;J=re.sub(G,'',A);C=next((A for A in D if re.sub(G,'',A[E].upper())==J),_B)
				B.symbol=C[E]if C else A
			except Exception:B.symbol=A
		B.data_source='Dukascopy';B.show_log=F
		if not F:logger.setLevel('CRITICAL')
	def _fetch_day_history(A,session,side):'Fetch the full daily candle history (one request).';C=f"{_BASE_URL}/candles/day/{A.symbol}/{side.upper()}";B=_safe_get(session,C);return _decode_candles(B,tz=A.timezone)if B else pd.DataFrame()
	def _fetch_minute_range(C,session,side,start_date,end_date):
		'Fetch per-day minute candles over a date range.';B=[];A=start_date
		while A<=end_date:
			E=f"{_BASE_URL}/candles/minute/{C.symbol}/{side.upper()}/{A.year}/{A.month}/{A.day}";D=_safe_get(session,E)
			if D:B.append(_decode_candles(D,tz=C.timezone))
			A+=datetime.timedelta(days=1)
		return pd.concat(B,ignore_index=_E)if B else pd.DataFrame()
	def _mid(E,df_bid,df_ask):
		'Compute mid-price from two equally-shaped bid/ask DataFrames.';B=df_ask;A=df_bid
		if A.empty:return pd.DataFrame()
		C=A.copy()
		if not B.empty and len(B)==len(A):
			for D in(_L,_M,_N,_O):C[D]=round((C[D]+B[D])/2,6)
		return C
	@agg_execution(_U)
	def history(self,start='',end='',interval='1d',side=_P,length=500,to_df=_E,**Z):
		"\n        Fetch historical OHLCV candlestick data.\n\n        Args:\n            start (str): Start date ``YYYY-MM-DD``. Leave blank to use ``length``.\n            end (str): End date ``YYYY-MM-DD``. Defaults to today (UTC).\n            interval (str): Timeframe – ``1m``, ``1h``, ``4h``, ``1d``, ``1w``, ``1M``.\n            side (str): Price side –\n                ``'bid'`` (default), ``'ask'``, or ``'mid'`` (bid+ask midpoint).\n            length (int): Maximum number of bars returned (tail truncation). Default 500.\n            to_df (bool): Return DataFrame (default) or JSON string.\n\n        Returns:\n            pd.DataFrame: ``[time, open, high, low, close, volume]``\n\n        Note:\n            - ``1h``, ``4h`` are resampled from 1-minute data (slower).\n            - ``1w``, ``1M`` are resampled from daily history.\n            - All timestamps are timezone-naive UTC.\n        ";T='left';S='ASK';R='BID';Q='mid';O=length;K=interval;J=end;G=start;B=self;C=K.strip();U={'1H':_C,'4H':_D,'1D':'1d','1W':'1w'};C=U.get(C.upper(),C.lower())
		if C==_F and K.endswith('M'):C='1M'
		if C not in _INTERVAL_FETCH:V=', '.join(_INTERVAL_FETCH);raise ValueError(f"Interval '{K}' not supported by Dukascopy. Supported: {V}")
		W,P=_INTERVAL_FETCH[C];H=side.lower();D=_session();L=datetime.datetime.utcnow().date()
		if J:
			E=pd.to_datetime(J).date()
			if E>=L:E=L-datetime.timedelta(days=1)
		else:E=L-datetime.timedelta(days=1)
		if W==_G:
			X={_F:1440,_C:24,_D:6}
			if not G:Y=max(5,O//X.get(C,24)+3);I=E-datetime.timedelta(days=Y)
			else:I=pd.to_datetime(G).date()
			F=E
			while F.weekday()>=5:F-=datetime.timedelta(days=1)
			if H==Q:M=B._fetch_minute_range(D,R,I,F);N=B._fetch_minute_range(D,S,I,F);A=B._mid(M,N)
			else:A=B._fetch_minute_range(D,H.upper(),I,F)
		elif H==Q:M=B._fetch_day_history(D,R);N=B._fetch_day_history(D,S);A=B._mid(M,N)
		else:A=B._fetch_day_history(D,H.upper())
		if A.empty:return pd.DataFrame()
		if P:A=A.set_index(_A);A=A.resample(P,label=T,closed=T).agg({_L:'first',_M:'max',_N:'min',_O:'last',_S:'sum'}).dropna().reset_index()
		A=A.sort_values(_A).reset_index(drop=_E)
		if G:A=A[A[_A]>=pd.to_datetime(G)]
		if J:A=A[A[_A]<=pd.to_datetime(E)+pd.Timedelta(days=1)]
		A=A.tail(O).reset_index(drop=_E)
		if hasattr(A[_A],'dt')and A[_A].dt.tz is not _B:A[_A]=A[_A].dt.tz_localize(_B)
		A.source=B.data_source;return A if to_df else A.to_json(orient=_T)
	@agg_execution(_U)
	def intraday(self,date='',hour=_B,to_df=_E,**I):
		'\n        Fetch tick-level data for a specific date and UTC hour.\n\n        Args:\n            date (str): Date ``YYYY-MM-DD``. Defaults to today (UTC).\n            hour (int | None): UTC hour (0–23). Defaults to the current UTC hour.\n            to_df (bool): Return DataFrame (default) or JSON string.\n\n        Returns:\n            pd.DataFrame: ``[time, ask, bid, price, ask_volume, bid_volume]``\n        ';B=self;F=_session();D=datetime.datetime.utcnow();C=pd.to_datetime(date).date()if date else D.date();G=hour if hour is not _B else D.hour;H=f"{_BASE_URL}/ticks/{B.symbol}/{C.year}/{C.month}/{C.day}/{G}";E=_safe_get(F,H)
		if not E:return pd.DataFrame()
		A=_decode_ticks(E,tz=B.timezone)
		if hasattr(A[_A],'dt')and A[_A].dt.tz is not _B:A[_A]=A[_A].dt.tz_localize(_B)
		A.source=B.data_source;return A if to_df else A.to_json(orient=_T)
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('quote','dukascopy',Quote)