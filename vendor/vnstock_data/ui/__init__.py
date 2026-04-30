'\nUI Module - Unified Interface for vnstock-data\n'
_G='show_doc'
_F='show_api'
_E='Analytics'
_D='Fundamental'
_C='Insights'
_B='Market'
_A='Reference'
from typing import TYPE_CHECKING,Any
if TYPE_CHECKING:from vnstock_data.ui.reference import Reference;from vnstock_data.ui.market import Market;from vnstock_data.ui.insights import Insights;from vnstock_data.ui.fundamental import Fundamental;from vnstock_data.ui.macro import Macro;from vnstock_data.ui.analytics import Analytics
__all__=[_A,_B,_C,_D,'Macro',_E,_F,_G]
def __getattr__(name):
	'\n    Lazy load UI modules using PEP 562. \n    Allows IDE autocomplete and type hints to work correctly.\n    ';A=name
	if A==_A:from vnstock_data.ui.reference import Reference as B;return B
	elif A==_B:from vnstock_data.ui.market import Market as C;return C
	elif A==_C:from vnstock_data.ui.insights import Insights as D;return D
	elif A==_D:from vnstock_data.ui.fundamental import Fundamental as E;return E
	elif A=='Macro':from vnstock_data.ui.macro import Macro as F;return F
	elif A==_E:from vnstock_data.ui.analytics import Analytics as G;return G
	elif A==_F:from vnstock_data.ui.helper import show_api as H;return H
	elif A==_G:from vnstock_data.ui.helper import show_doc as I;return I
	raise AttributeError(f"module {__name__!r} has no attribute {A!r}")