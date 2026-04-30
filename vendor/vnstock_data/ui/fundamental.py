'\nFundamental Module Entry Point (Layer 3).\n'
from vnstock_data.ui.domains.fundamental.equity import EquityFundamental
import pandas as pd
class EquityFundamentalProxy:
	'\n    Proxy to support both:\n    1. fun.equity("TCB").cash_flow(...)\n    2. fun.equity.cash_flow("TCB", ...)\n    '
	def __call__(A,symbol):return EquityFundamental(symbol)
	def ratio(B,symbol,**A):return EquityFundamental(symbol).ratio(**A)
	def income_statement(B,symbol,**A):return EquityFundamental(symbol).income_statement(**A)
	def balance_sheet(B,symbol,**A):return EquityFundamental(symbol).balance_sheet(**A)
	def cash_flow(B,symbol,**A):return EquityFundamental(symbol).cash_flow(**A)
	def note(B,symbol,**A):return EquityFundamental(symbol).note(**A)
	def financial_health(B,symbol,scorecard='auto',**A):'\n        Combines Income Statement, Balance Sheet, and Ratios into a single summarized matrix using TCBS scorecard conventions.\n        ';return EquityFundamental(symbol).financial_health(scorecard=scorecard,**A)
class Fundamental:
	"\n    Central API Gateway for Layer 3 - Fundamental Data (Unified UI).\n    Provides financial statements, ratios, and diagnostic analysis for equities.\n    \n    ✅ METHODS AVAILABLE (5 total):\n    \n    equity(symbol) → EquityFundamental object with 5 methods:\n        - ratio()               → Financial ratios (P/E, ROE, Debt/Equity, etc.)\n        - income_statement()    → Revenue, expenses, profit (quarterly/annual)\n        - balance_sheet()       → Assets, liabilities, equity position\n        - cash_flow()           → Operating, investing, financing cash flows\n        - note()                → Footnotes and disclosures (Thuyết minh)\n    \n    Example:\n        fund = Fundamental()\n        vic = fund.equity('VIC')\n        \n        ratios = vic.ratio()                    # 12 periods\n        income = vic.income_statement()         # 12 periods\n        balance = vic.balance_sheet()           # 12 periods\n        cash = vic.cash_flow()                  # 12 periods\n        notes = vic.note()                      # All footnotes\n    "
	@property
	def equity(self):"\n        Access financial data for a specific corporate equity (Fundamental Layer).\n        \n        Args:\n            symbol (str): The stock ticker symbol (e.g. 'VIC', 'VNM', 'FPT')\n            \n        Returns:\n            EquityFundamental: Object with 5 methods for financial analysis:\n                - ratio()          - Key financial ratios\n                - income_statement()- Income statement (12+ periods)\n                - balance_sheet()  - Balance sheet (12+ periods)\n                - cash_flow()      - Cash flow statement (12+ periods)\n                - note()           - Financial disclosures/footnotes\n        \n        Example:\n            fund = Fundamental()\n            vic_data = fund.equity('VIC')\n            ratios = vic_data.ratio()\n        ";return EquityFundamentalProxy()