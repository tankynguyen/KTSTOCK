'\nIndex Market Data Domain.\n'
_A=None
from vnstock_data.ui.domains.market.base import BaseMarketData
from vnstock_data.ui._registry import MARKET_SOURCES
import pandas as pd
class IndexMarket(BaseMarketData):
	'\n    Index Market Data (Layer 2).\n    ';trades=_A;intraday=_A;order_book=_A;price_depth=_A
	def __init__(I,symbol,**A):
		G='Quote';F='quote';E='dukascopy';D='intraday';C='market.index';H=A.pop('scope','');B=MARKET_SOURCES.copy()
		if H=='global':B[C]={'ohlcv':(E,F,G,'history'),D:(E,F,G,D)}
		super().__init__(symbol=symbol,domain_name=C,layer_sources=B,**A)
	def trade_history(A,**B):'\n        Historical trading statistics (price, volume, value) for Indices.\n        ';return A._dispatch('price_history',**B)