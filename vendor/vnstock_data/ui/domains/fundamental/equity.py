'\nEquity Fundamental Domain (Layer 3).\nWraps the `kbs.financial.Finance` module.\n'
_K='cash_flow'
_J='balance_sheet'
_I='income_statement'
_H='lang'
_G='display_mode'
_F='banking'
_E=True
_D=False
_C='ticker'
_B='period'
_A=None
import pandas as pd
from vnstock_data.ui._base import BaseDetail
from vnstock_data.ui.schemas.core import standardize_columns
from vnstock_data.ui._registry import FUNDAMENTAL_SOURCES
class EquityFundamental(BaseDetail):
	'\n    Access point for fetching company financial statements and valuation ratios.\n    '
	def __init__(A,symbol):super().__init__(symbol=symbol,domain_name='equity.fundamental',layer_sources=FUNDAMENTAL_SOURCES)
	def _resolve_scorecard(K,scorecard):
		'Resolves auto scorecard into exact sector keys based on literal text definitions';J='sector';I='industry';H='securities';G='bank';D='insurance';B=scorecard;E={G:_F,'sec':H,'ins':D}
		if B in E:B=E[B]
		if B=='auto':
			from vnstock_data.ui import Reference as L
			try:
				C=L().company(K.symbol).info()
				if not C.empty:
					F=I if I in C.columns else J if J in C.columns else _A
					if F:
						A=str(C[F].iloc[0])
						if A.startswith('Ngân hàng')or G in A.lower():return _F
						elif A.startswith('Dịch vụ tài chính')or'chứng khoán'in A.lower()or'financial services'in A.lower():return H
						elif'Bảo hiểm'in A or D in A.lower():return D
			except Exception:pass
			return'generic'
		return B
	def _dispatch_and_format(C,method_name,scorecard=_A,filter_unmapped=_A,**H):
		'\n        Dispatches method to KBS Finance and standardizes columns without strict trimming.\n        Financial statements vary widely depending on sector, so we use `strict=False`\n        to preserve all snake_cased accounting fields.\n        ';M='item_id';F=filter_unmapped;D=method_name;E=H.copy()
		if _G not in E:from vnstock_data.explorer.kbs.financial import FieldDisplayMode as N;E[_G]=N.STD
		E.pop(_H,_A);A=C._dispatch(D,**E)
		if A.empty:return A
		from vnstock_data.ui.config import get_route as O;P,I,I,I=O(C._domain_name,D,C._sources_config);J='fundamental.equity';G=C._resolve_scorecard(scorecard)
		if F is _A:F=G is not _A
		A=standardize_columns(A,f"{J}.{D}",P,strict=_D,filter_unmapped=F)
		if M in A.columns:
			B=A.set_index(M);K=[A for A in B.columns if str(A).replace('-','Q').replace('Q','1').isdigit()]
			if K:B=B[K].transpose();B=B.reset_index();B=B.rename(columns={'index':_B});B.insert(1,_C,C.symbol);A=B.sort_values(_B).reset_index(drop=_E)
		A=A.loc[:,~A.columns.duplicated(keep='first')]
		if G:
			from vnstock_data.ui.schemas.scorecards import SCORECARDS as Q;L=Q.get(G,{}).get(f"{J}.{D}",[])
			if L:R=[A for A in A.columns if A in L or A in[_B,_C,'report_period']];A=A[R]
		if H.get(_H)=='vi':from vnstock_data.ui.schemas.dictionary import FUNDAMENTAL_VI_LABELS as S;A=A.rename(columns=S)
		return A
	def ratio(A,scorecard=_A,**B):'\n        Extracts key financial ratios (P/E, ROE, Debt/Equity, etc.).\n        \n        Returns:\n            pd.DataFrame: Ratios pivoted by period.\n        ';return A._dispatch_and_format('ratio',scorecard=scorecard,**B)
	def income_statement(A,scorecard=_A,**B):'\n        Extracts Income Statement.\n        ';return A._dispatch_and_format(_I,scorecard=scorecard,**B)
	def balance_sheet(A,scorecard=_A,**B):'\n        Extracts Balance Sheet.\n        ';return A._dispatch_and_format(_J,scorecard=scorecard,**B)
	def cash_flow(A,scorecard=_A,**B):'\n        Extracts Cash Flow statement.\n        ';return A._dispatch_and_format(_K,scorecard=scorecard,**B)
	def note(A,**C):
		"\n        Extracts Footnotes (Thuyết minh Báo cáo tài chính).\n        Note: This method doesn't accept display_mode parameter.\n        ";E='note';C.pop(_G,_A);B=A._dispatch(E,**C)
		if B.empty:return B
		from vnstock_data.ui.config import get_route as F;from vnstock_data.ui.schemas.core import standardize_columns as G;H,D,D,D=F(A._domain_name,E,A._sources_config);return G(B,f"{A._domain_name}.note",H,strict=_D,filter_unmapped=_D)
	def financial_health(C,scorecard='auto',reports=_A,**E):
		'\n        Aggregates Balance Sheet, Income Statement, Cash Flow, and Ratios into a single unified health matrix\n        with TCBS-style section headers and proper field ordering.\n        \n        Args:\n            scorecard: \'auto\' (detect via ICB), \'banking\', \'securities\', \'insurance\', \'generic\'.\n            reports: A list specifying which datasets to merge. Defaults to all 4 fundamental reports.\n                     Options: ["income_statement", "balance_sheet", "cash_flow", "ratio"]\n        ';I=scorecard;D=reports;print('\x1b[93m'+'⚠️ MIỄN TRỪ TRÁCH NHIỆM: Dữ liệu tài chính được chuẩn hóa và tổng hợp dựa trên các nguồn thông tin công khai. Mặc dù cấu trúc báo cáo được thiết kế dựa trên tiêu chuẩn tham chiếu từ hệ thống phân tích của TCBS nhằm đảm bảo tính nhất quán, người dùng cần lưu ý rằng do sự khác biệt trong phương pháp hạch toán và độ trễ dữ liệu giữa các nguồn, các chỉ số có thể tồn tại sai số hoặc khác biệt so với các nền tảng tham chiếu khác. Thông tin này chỉ mang tính chất tham khảo. Người dùng cam kết tự rà soát và chịu toàn bộ trách nhiệm đối với mọi quyết định sử dụng dữ liệu này trong các hoạt động đầu tư.'+'\x1b[0m');F=[]
		if D is _A:D=[_I,_J,_K,'ratio']
		for L in D:
			M=getattr(C,L);B=M(scorecard=I,**E)
			if not B.empty:
				if _C in B.columns:B=B.drop(columns=[_C])
				F.append(B.set_index(_B))
		if not F:return pd.DataFrame()
		G=pd.concat(F,axis=1,join='outer');G=G.T.groupby(level=0).sum(min_count=1).T.reset_index();J=C._resolve_scorecard(I);A=C._apply_tcbs_ordering(G,J,**E)
		if J==_F:
			from vnstock_data.ui.schemas.dictionary import FUNDAMENTAL_VI_LABELS,FundamentalKeys as O;N={'net_interest_income':'Thu nhập lãi thuần','net_fee_and_commission_income':'Lãi thuần từ HĐ dịch vụ','net_gain_loss_from_investment_activities':'Lãi thuần từ HĐ đầu tư','net_other_income':'Lãi thuần từ HĐ khác'};K=[B for B in N.values()if B in A.columns]
			if len(K)>=2:A['Tổng thu nhập HĐ (TOI)']=A[K].sum(axis=1,min_count=1)
		H=E.get('limit',16)
		if H and H>0:A=A.sort_values(by=_B,ascending=_D);A=A.head(H);A=A.sort_values(by=_B,ascending=_E)
		else:A=A.sort_values(by=_B,ascending=_E)
		A.insert(0,_C,C.symbol);return A
	def _apply_tcbs_ordering(T,df,scorecard_key,**M):
		'\n        Apply TCBS-style section headers and field ordering to the financial health data.\n        Creates a structured output with section headers as index values.\n        ';A=df;from vnstock_data.ui.schemas.scorecards import get_financial_health_sections as N;from vnstock_data.ui.schemas.dictionary import FUNDAMENTAL_VI_LABELS as O;P=N(scorecard_key);D=[]
		for H in P:
			Q=H['header'];R=H['fields'];I=_D;J=[]
			for E in R:
				B=_A
				if E in A.columns:B=E
				elif M.get(_H)=='vi':
					F=O.get(E)
					if F and F in A.columns:B=F
				if B:I=_E;J.append(B)
			if I:D.append(Q);D.extend(J)
		G=[]
		for K in D:
			if K in A.columns:G.append(K)
		if G:
			C=[]
			if _B in A.columns:C.append(_B)
			if _C in A.columns:C.append(_C)
			S=C+[A for A in G if A not in C];L=A[S].copy()
		else:L=A.copy()
		return L