'\nMarket Reference domain.\n'
import pandas as pd
from typing import Optional
from vnstock_data.ui._base import BaseDomain
from vnstock_data.ui._registry import REFERENCE_SOURCES
class MarketReference(BaseDomain):
	'\n    Market Reference Data.\n    Provides access to live market status.\n    '
	def __init__(A):super().__init__(domain_name='market',layer_sources=REFERENCE_SOURCES)
	def status(A,**B):'\n        Retrieve live stock market status (OPEN, CLOSED, ATO, ATC, etc.)\n        from the default data source.\n        \n        Returns:\n            pd.DataFrame: Live market status for various exchanges.\n        ';return A._dispatch('status',**B)