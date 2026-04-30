'Financial module for KB Securities (KBS) data source.'
_Z='ignore'
_Y='LCTT'
_X='financial_ratios'
_W='cash_flow'
_V='balance_sheet'
_U='income_statement'
_T='KBS.ext'
_S='period'
_R='report_type'
_Q='source'
_P='symbol'
_O='annual'
_N='Content'
_M='row_number'
_L='levels'
_K='quarter'
_J='unit'
_I='item_en'
_H='item'
_G='unit_type'
_F='audit_status'
_E=None
_D='year'
_C='periods'
_B=False
_A='item_id'
import json,pandas as pd
from typing import Optional,List,Dict,Tuple,Union
from enum import Enum
from vnai import agg_execution
import logging
from vnstock_data.core.utils.parser import get_asset_type,vn_to_snake_case
from vnstock_data.core.utils.client import send_request,ProxyConfig
from vnstock_data.core.utils.user_agent import get_headers
from vnstock_data.explorer.kbs.const import _SAS_FINANCE_INFO_URL,_INCOME_STATEMENT_MAP,_BALANCE_SHEET_MAP,_CASH_FLOW_MAP,_FINANCIAL_RATIOS_MAP,_FINANCIAL_REPORT_TYPE_MAP,_FINANCIAL_PERIOD_TYPE_MAP
logger=logging.getLogger(__name__)
class FieldDisplayMode(Enum):'Field display modes.';STD='std';ALL='all';AUTO='auto'
class Finance:
	'\n    Lớp truy cập dữ liệu tài chính từ KB Securities (KBS).\n    '
	def __init__(A,symbol,period=_E,random_agent=_B,proxy_config=_E,show_log=_B,standardize_columns=True,proxy_mode=_E,proxy_list=_E):
		"\n        Khởi tạo Finance client cho KBS.\n\n        Args:\n            symbol: Mã chứng khoán (VD: 'ACB', 'VNM').\n            period: Kỳ báo cáo mặc định ('year', 'quarter' hoặc None).\n            random_agent: Sử dụng user agent ngẫu nhiên. Mặc định False.\n            proxy_config: Cấu hình proxy. Mặc định None.\n            show_log: Hiển thị log debug. Mặc định False.\n            standardize_columns: Chuẩn hoá tên cột theo schema. Mặc định True.\n            proxy_mode: Chế độ proxy (try, rotate, random, single). Mặc định None.\n            proxy_list: Danh sách proxy URLs. Mặc định None.\n\n        Raises:\n            ValueError: Nếu mã không phải là cổ phiếu.\n        ";F=proxy_mode;E=show_log;D=proxy_config;C=proxy_list;B=period;A.symbol=symbol.upper();A.asset_type=get_asset_type(A.symbol)
		if B is not _E and B not in[_D,_K]:raise ValueError("Kỳ báo cáo tài chính không hợp lệ. Chỉ chấp nhận 'year' hoặc 'quarter' hoặc None.")
		A.period=B
		if A.asset_type not in['stock']:raise ValueError('Mã CK không hợp lệ hoặc không phải cổ phiếu.')
		A.data_source='KBS';A.headers=get_headers(data_source=A.data_source,random_agent=random_agent);A.show_log=E;A.standardize_columns=standardize_columns
		if D is _E:
			H=F if F else'try';G='direct'
			if C and len(C)>0:G='proxy'
			A.proxy_config=ProxyConfig(proxy_mode=H,proxy_list=C,request_mode=G)
		else:A.proxy_config=D
		if E:logger.setLevel('INFO')
		else:logger.setLevel('CRITICAL')
	def _get_column_mapping(B,report_type):'\n        Lấy column mapping cho loại báo cáo.\n        \n        Args:\n            report_type: Loại báo cáo (income_statement, balance_sheet, cash_flow, financial_ratios)\n            \n        Returns:\n            Dictionary chứa mapping từ cột gốc sang cột chuẩn hoá\n        ';A={_U:_INCOME_STATEMENT_MAP,_V:_BALANCE_SHEET_MAP,_W:_CASH_FLOW_MAP,_X:_FINANCIAL_RATIOS_MAP};return A.get(report_type,{})
	def _parse_financial_response(t,response,report_key,include_metadata=_B):
		"\n        Parse KBS API response and extract financial data with proper structure.\n        \n        Args:\n            response: API response containing Audit, Unit, Head, Content\n            report_key: Key in Content (e.g., 'Kết quả kinh doanh')\n            include_metadata: Whether to include Audit and Unit info as rows in DataFrame\n            \n        Returns:\n            DataFrame with proper financial data structure\n        ";k='Quý';j='Unit';X=report_key;G=response;B='';Y=G.get('Audit',[]);Z=G.get(j,[]);a=G.get('Head',[]);l=G.get(_N,{});b=l.get(X,[])
		if not b:return pd.DataFrame()
		H=[];O={};P={}
		if a:
			m=sorted(a,key=lambda x:x.get('ID',0))
			for F in m:
				if isinstance(F,dict):
					c=F.get('YearPeriod',B);Q=F.get('TermName',B)
					if Q and k in Q:n=Q.replace(k,B).strip();D=f"{c}-Q{n}"
					else:D=str(c)
					H.append(D);O[D]=F.get('AuditedStatus',B);P[D]=F.get('United',B)
		R={}
		if Y:
			for S in Y:
				if isinstance(S,dict):R[S.get('AuditedStatusCode')]=S.get('Description')
		T={}
		if Z:
			for U in Z:
				if isinstance(U,dict):T[U.get('UnitedCode')]=U.get('UnitedName')
		I=[];J={}
		for E in b:
			K=E.get('Name',B);L=E.get('NameEn',B)
			if L and L.strip():A=vn_to_snake_case(L)
			elif K and K.strip():A=vn_to_snake_case(K)
			else:A=B
			if A and A in J:J[A]+=1;A=A+'_'+str(J[A])
			elif A:J[A]=1
			d={_H:K,_I:L,_A:A,_J:E.get(j,B),_L:E.get('Levels',0),_M:E.get('ID',0)}
			for(o,D)in enumerate(H,1):
				p=f"Value{o}";M=E.get(p)
				if M is not _E:
					try:M=float(M)
					except(ValueError,TypeError):pass
				d[D]=M
			I.append(d)
		if include_metadata:
			e={_H:'Kiểm toán',_I:'Audit Status',_A:_F,_J:B,_L:0,_M:-2};f={_H:'Đơn vị',_I:'Unit Type',_A:_G,_J:B,_L:0,_M:-1}
			for N in H:g=O.get(N);e[N]=R.get(g,g);h=P.get(N);f[N]=T.get(h,h)
			I.append(e);I.append(f)
		C=pd.DataFrame(I);q=[_H,_I,_A,_J,_L,_M];r=[A for A in q if A in C.columns];s=[A for A in H if A in C.columns];V=[]
		for i in s:
			if not C[i].isnull().all():V.append(i)
		C=C[r+V];W=V;C.attrs[_F]={A:R.get(B,B)for(A,B)in O.items()if A in W};C.attrs[_G]={A:T.get(B,B)for(A,B)in P.items()if A in W};C.attrs[_C]=W;C.attrs['report_key']=X;return C
	def _apply_schema_standardization(B,df,report_type):
		'\n        Áp dụng chuẩn hoá schema cho DataFrame.\n        \n        Args:\n            df: DataFrame cần chuẩn hoá\n            report_type: Loại báo cáo\n            \n        Returns:\n            DataFrame với dữ liệu chuẩn hoá\n        ';A=df
		if not B.standardize_columns or A.empty:return A
		C=B._get_column_mapping(report_type)
		if _A in A.columns and C:
			E=A[_A].isin(C.keys());D=E.sum()
			if D>0:
				A[_A]=A[_A].replace(C)
				if B.show_log:logger.info(f"Applied schema standardization: {D} items standardized")
		return A
	def _filter_columns_by_lang(G,df,display_mode=FieldDisplayMode.STD):
		"\n        Filter DataFrame columns based on field display mode.\n        \n        Args:\n            df: DataFrame to filter\n            display_mode: Field display mode\n                - FieldDisplayMode.STD: Keep only 'item' and 'item_id' columns (standardized)\n                - FieldDisplayMode.ALL: Keep all item columns (item, item_en, item_id)\n                - FieldDisplayMode.AUTO: Auto-convert based on data type\n                - 'vi': Keep Vietnamese names only (backward compatibility)\n                - 'en': Keep English names only (backward compatibility)\n                - None: Keep all item columns (backward compatibility)\n            \n        Returns:\n            DataFrame with filtered columns\n        ";C=df;A=display_mode
		if C.empty:return C
		if isinstance(A,str):
			if A=='vi':A=FieldDisplayMode.STD
			elif A=='en':A=FieldDisplayMode.STD
			else:A=FieldDisplayMode.ALL
		F=C.attrs.get(_C,[]);E=[A for A in C.columns if A not in F];D=C.copy()
		if A==FieldDisplayMode.ALL:B=E
		elif A==FieldDisplayMode.AUTO:B=E
		else:
			B=[A for A in E if A in[_H,_A]]
			if isinstance(A,str)and A=='en'and _I in D.columns:D[_H]=D[_I];B=[_H,_A]
		B.extend(F);B=[A for A in B if A in D.columns];return D[B]
	def _fetch_financial_data(A,report_type='KQKD',period_type=1,page=1,page_size=4,show_log=_B):
		'\n        Lấy dữ liệu tài chính từ API SAS với các tham số chính xác.\n\n        Args:\n            report_type: Loại báo cáo (CDKT, KQKD, LCTT, CSTC, CTKH, BCTT)\n            period_type: Loại kỳ báo cáo (1=năm, 2=quý)\n            page: Trang (mặc định 1)\n            page_size: Số bản ghi trên trang (mặc định 4)\n            show_log: Hiển thị log debug.\n\n        Returns:\n            Dictionary chứa dữ liệu tài chính đầy đủ.\n        ';G='data';F=period_type;E=report_type;B=show_log;H=f"{_SAS_FINANCE_INFO_URL}/{A.symbol}";C={'page':page,'pageSize':page_size,'type':E,_J:1000,'termtype':F}
		if E!=_Y:C['languageid']=1
		else:C['code']=A.symbol;C['termType']=F
		if B or A.show_log:logger.info(f"KBS Financial API Request: {A.symbol} - {E} - Period: {F}")
		try:
			D=send_request(url=H,headers=A.headers,method='GET',params=C,show_log=B or A.show_log,proxy_list=A.proxy_config.proxy_list,proxy_mode=A.proxy_config.proxy_mode,request_mode=A.proxy_config.request_mode)
			if B or A.show_log:
				if isinstance(D,dict)and G in D:logger.info('API Response received: '+str(len(D.get(G,[])))+' records')
			return D
		except Exception as I:
			if B or A.show_log:logger.error(f"API Request Failed: {str(I)}")
			raise
	def _fetch_series_data(H,report_type,period_type,report_key,limit=12,include_metadata=_B,show_log=_B):
		'\n        Helper to fetch data across multiple pages to satisfy the limit.\n        ';C=limit;D=[];I=[];E=1;L=max(C,4)
		while len(I)<C:
			M=H._fetch_financial_data(report_type=report_type,period_type=period_type,page=E,page_size=L,show_log=show_log);F=H._parse_financial_response(M,report_key,include_metadata=include_metadata)
			if F.empty:break
			J=F.attrs.get(_C,[])
			if not J:break
			D.append(F);I.extend(J);E+=1
			if E>50:break
		if not D:return pd.DataFrame()
		A=D[0];S=[_H,_I,_A,_J,_L,_M]
		for N in range(1,len(D)):
			B=D[N];K=B.attrs[_C];O=[_A]+K
			if _A in B.columns:
				P=A.attrs;A=pd.merge(A,B[O],on=_A,how='outer');A.attrs=P
				if _F in B.attrs:
					if _F not in A.attrs:A.attrs[_F]={}
					A.attrs[_F].update(B.attrs[_F])
				if _G in B.attrs:
					if _G not in A.attrs:A.attrs[_G]={}
					A.attrs[_G].update(B.attrs[_G])
				if _C in A.attrs:A.attrs[_C].extend(K)
		G=A.attrs[_C]
		if len(G)>C:Q=G[:C];R=G[C:];A=A.drop(columns=R,errors=_Z);A.attrs[_C]=Q
		return A
	@agg_execution(_T)
	def income_statement(self,period=_E,limit=12,include_metadata=_B,display_mode=FieldDisplayMode.STD,show_log=_B):
		"\n        Truy xuất báo cáo kết quả kinh doanh (income statement).\n\n        Args:\n            period: Loại kỳ báo cáo ('year' hoặc 'quarter'). Mặc định 'year'.\n            limit: Số kỳ báo cáo tối đa cần lấy. Mặc định 4.\n            include_metadata: Bao gồm thông tin audit và unit trong rows. Mặc định False.\n            display_mode: Chế độ hiển thị trường dữ liệu. Mặc định FieldDisplayMode.STD.\n                - FieldDisplayMode.STD: Chỉ giữ cột 'item' và 'item_id' (đã chuẩn hóa)\n                - FieldDisplayMode.ALL: Giữ tất cả cột item (item, item_en, item_id)\n                - 'vi': Chỉ giữ tên tiếng Việt (tương thích ngược)\n                - 'en': Chỉ giữ tên tiếng Anh (tương thích ngược)\n                - None: Giữ tất cả cột (tương thích ngược)\n            show_log: Hiển thị log debug.\n\n        Returns:\n            DataFrame chứa báo cáo kết quả kinh doanh.\n\n        Examples:\n            >>> finance = Finance('ACB')\n            >>> df = finance.income_statement(period='year', display_mode=FieldDisplayMode.STD)\n            >>> # Returns DataFrame with columns: item, item_id, unit, periods...\n            >>> df_all = finance.income_statement(period='year', display_mode=FieldDisplayMode.ALL)\n            >>> # Returns DataFrame with all item columns\n            >>> # Backward compatibility:\n            >>> df_vi = finance.income_statement(period='year', display_mode='vi')\n            >>> df_en = finance.income_statement(period='year', display_mode='en')\n        ";E=show_log;D=period;A=self;C=D if D else A.period if A.period else _D;G=str(C).lower()
		if G in[_D,'y',_O]:C=_D;F=1
		else:C=_K;F=2
		B=A._fetch_series_data(report_type='KQKD',period_type=F,report_key='Kết quả kinh doanh',limit=limit,include_metadata=include_metadata,show_log=E)
		if B.empty:logger.warning(f"Không tìm thấy báo cáo kết quả kinh doanh cho {A.symbol}.");return pd.DataFrame()
		if A.standardize_columns:B=A._apply_schema_standardization(B,_U)
		B=A._filter_columns_by_lang(B,display_mode);B.attrs[_P]=A.symbol;B.attrs[_Q]=A.data_source;B.attrs[_R]=_U;B.attrs[_S]=C
		if E or A.show_log:logger.info(f"Truy xuất thành công báo cáo kết quả kinh doanh cho {A.symbol}.")
		return B
	@agg_execution(_T)
	def balance_sheet(self,period=_E,limit=12,include_metadata=_B,display_mode=FieldDisplayMode.STD,show_log=_B):
		"\n        Truy xuất bảng cân đối kế toán (balance sheet).\n\n        Args:\n            period: Loại kỳ báo cáo ('year' hoặc 'quarter'). Mặc định 'year'.\n            limit: Số kỳ báo cáo tối đa cần lấy. Mặc định 4.\n            include_metadata: Bao gồm thông tin audit và unit trong rows. Mặc định False.\n            display_mode: Chế độ hiển thị trường dữ liệu. Mặc định FieldDisplayMode.STD.\n                - FieldDisplayMode.STD: Chỉ giữ cột 'item' và 'item_id' (đã chuẩn hóa)\n                - FieldDisplayMode.ALL: Giữ tất cả cột item (item, item_en, item_id)\n                - 'vi': Chỉ giữ tên tiếng Việt (tương thích ngược)\n                - 'en': Chỉ giữ tên tiếng Anh (tương thích ngược)\n                - None: Giữ tất cả cột (tương thích ngược)\n            show_log: Hiển thị log debug.\n\n        Returns:\n            DataFrame chứa bảng cân đối kế toán.\n\n        Examples:\n            >>> finance = Finance('ACB')\n            >>> df = finance.balance_sheet(period='year', display_mode=FieldDisplayMode.STD)\n            >>> df_all = finance.balance_sheet(period='year', display_mode=FieldDisplayMode.ALL)\n            >>> # Backward compatibility:\n            >>> df_vi = finance.balance_sheet(period='year', display_mode='vi')\n            >>> df_en = finance.balance_sheet(period='year', display_mode='en')\n        ";E=show_log;D=period;A=self;C=D if D else A.period if A.period else _D;G=str(C).lower()
		if G in[_D,'y',_O]:C=_D;F=1
		else:C=_K;F=2
		B=A._fetch_series_data(report_type='CDKT',period_type=F,report_key='Cân đối kế toán',limit=limit,include_metadata=include_metadata,show_log=E)
		if B.empty:logger.warning(f"Không tìm thấy bảng cân đối kế toán cho {A.symbol}.");return pd.DataFrame()
		if A.standardize_columns:B=A._apply_schema_standardization(B,_V)
		B=A._filter_columns_by_lang(B,display_mode);B.attrs[_P]=A.symbol;B.attrs[_Q]=A.data_source;B.attrs[_R]=_V;B.attrs[_S]=C
		if E or A.show_log:logger.info(f"Truy xuất thành công bảng cân đối kế toán cho {A.symbol}.")
		return B
	@agg_execution(_T)
	def cash_flow(self,period=_E,limit=12,include_metadata=_B,display_mode=FieldDisplayMode.STD,show_log=_B):
		"\n        Truy xuất báo cáo lưu chuyển tiền tệ (cash flow statement).\n\n        Args:\n            period: Loại kỳ báo cáo ('year' hoặc 'quarter'). Mặc định 'year'.\n            limit: Số kỳ báo cáo tối đa cần lấy. Mặc định 4.\n            include_metadata: Bao gồm thông tin audit và unit trong rows. Mặc định False.\n            display_mode: Chế độ hiển thị trường dữ liệu. Mặc định FieldDisplayMode.STD.\n                - FieldDisplayMode.STD: Chỉ giữ cột 'item' và 'item_id' (đã chuẩn hóa)\n                - FieldDisplayMode.ALL: Giữ tất cả cột item (item, item_en, item_id)\n                - 'vi': Chỉ giữ tên tiếng Việt (tương thích ngược)\n                - 'en': Chỉ giữ tên tiếng Anh (tương thích ngược)\n                - None: Giữ tất cả cột (tương thích ngược)\n            show_log: Hiển thị log debug.\n\n        Returns:\n            DataFrame chứa báo cáo lưu chuyển tiền tệ.\n\n        Examples:\n            >>> finance = Finance('ACB')\n            >>> df = finance.cash_flow(period='year', display_mode=FieldDisplayMode.STD)\n            >>> df_all = finance.cash_flow(period='year', display_mode=FieldDisplayMode.ALL)\n            >>> # Backward compatibility:\n            >>> df_vi = finance.cash_flow(period='year', display_mode='vi')\n            >>> df_en = finance.cash_flow(period='year', display_mode='en')\n        ";K='Lưu chuyển tiền tệ trực tiếp';J='Lưu chuyển tiền tệ gián tiếp';G=show_log;F=period;A=self;C=F if F else A.period if A.period else _D;L=str(C).lower()
		if L in[_D,'y',_O]:C=_D;E=1
		else:C=_K;E=2
		H=A._fetch_financial_data(report_type=_Y,period_type=E,page_size=1,show_log=_B)
		if not H:raise ValueError(f"Không tìm thấy dữ liệu tài chính cho mã {A.symbol}.")
		I=H.get(_N,{});D=_E
		if J in I:D=J
		elif K in I:D=K
		if not D:logger.warning(f"Không tìm thấy báo cáo lưu chuyển tiền tệ cho {A.symbol}.");return pd.DataFrame()
		B=A._fetch_series_data(report_type=_Y,period_type=E,report_key=D,limit=limit,include_metadata=include_metadata,show_log=G)
		if B.empty:logger.warning(f"Không tìm thấy báo cáo lưu chuyển tiền tệ cho {A.symbol}.");return pd.DataFrame()
		if A.standardize_columns:B=A._apply_schema_standardization(B,_W)
		B=A._filter_columns_by_lang(B,display_mode);B.attrs[_P]=A.symbol;B.attrs[_Q]=A.data_source;B.attrs[_R]=_W;B.attrs[_S]=C
		if G or A.show_log:logger.info(f"Truy xuất thành công báo cáo lưu chuyển tiền tệ cho {A.symbol}.")
		return B
	@agg_execution(_T)
	def ratio(self,period=_E,limit=12,include_metadata=_B,display_mode=FieldDisplayMode.STD,show_log=_B):
		"\n        Truy xuất các chỉ số tài chính (financial ratios).\n\n        Args:\n            period: Loại kỳ báo cáo ('year' hoặc 'quarter'). Mặc định 'year'.\n            limit: Số kỳ báo cáo tối đa cần lấy. Mặc định 4.\n            include_metadata: Bao gồm thông tin audit và unit trong rows. Mặc định False.\n            display_mode: Chế độ hiển thị trường dữ liệu. Mặc định FieldDisplayMode.STD.\n                - FieldDisplayMode.STD: Chỉ giữ cột 'item' và 'item_id' (đã chuẩn hóa)\n                - FieldDisplayMode.ALL: Giữ tất cả cột item (item, item_en, item_id)\n                - 'vi': Chỉ giữ tên tiếng Việt (tương thích ngược)\n                - 'en': Chỉ giữ tên tiếng Anh (tương thích ngược)\n                - None: Giữ tất cả cột (tương thích ngược)\n# Register provider\nfrom vnstock_data.core.registry import ProviderRegistry\nProviderRegistry.register('financial', 'kbs', Finance)\n\n\n        Returns:\n            DataFrame chứa các chỉ số tài chính.\n\n        Examples:\n            >>> finance = Finance('ACB')\n            >>> df = finance.ratio(period='year', display_mode=FieldDisplayMode.STD)\n            >>> df_all = finance.ratio(period='year', display_mode=FieldDisplayMode.ALL)\n            >>> # Backward compatibility:\n            >>> df_vi = finance.ratio(period='year', display_mode='vi')\n            >>> df_en = finance.ratio(period='year', display_mode='en')\n        ";S='Financial Ratios Combined';M=show_log;L=period;D=limit;B=self;F=L if L else B.period if B.period else _D;T=str(F).lower()
		if T in[_D,'y',_O]:F=_D;N=1
		else:F=_K;N=2
		E=[];O=[];H=1;U=max(D,4)
		while len(O)<D:
			G=B._fetch_financial_data(report_type='CSTC',period_type=N,page=H,page_size=U,show_log=M)
			if not G:break
			V=G.get(_N,{});W=['Nhóm chỉ số Định giá','Nhóm chỉ số Sinh lợi','Nhóm chỉ số Tăng trưởng','Nhóm chỉ số Thanh khoản','Nhóm chỉ số Chất lượng tài sản'];I=[]
			for X in W:
				P=V.get(X,[])
				if P:I.extend(P)
			if not I:break
			G[_N][S]=I;J=B._parse_financial_response(G,S,include_metadata=include_metadata)
			if J.empty:break
			Q=J.attrs.get(_C,[])
			if not Q:break
			E.append(J);O.extend(Q);H+=1
			if H>50:break
		if not E:logger.warning(f"Không tìm thấy chỉ số tài chính cho {B.symbol}.");return pd.DataFrame()
		A=E[0]
		for Y in range(1,len(E)):
			C=E[Y];R=C.attrs[_C];Z=[_A]+R
			if _A in C.columns:
				a=A.attrs;A=pd.merge(A,C[Z],on=_A,how='outer');A.attrs=a
				if _F in C.attrs:
					if _F not in A.attrs:A.attrs[_F]={}
					A.attrs[_F].update(C.attrs[_F])
				if _G in C.attrs:
					if _G not in A.attrs:A.attrs[_G]={}
					A.attrs[_G].update(C.attrs[_G])
				if _C in A.attrs:A.attrs[_C].extend(R)
		K=A.attrs[_C]
		if len(K)>D:b=K[:D];c=K[D:];A=A.drop(columns=c,errors=_Z);A.attrs[_C]=b
		if B.standardize_columns:A=B._apply_schema_standardization(A,_X)
		A=B._filter_columns_by_lang(A,display_mode);A.attrs[_P]=B.symbol;A.attrs[_Q]=B.data_source;A.attrs[_R]=_X;A.attrs[_S]=F
		if M or B.show_log:logger.info(f"Truy xuất thành công chỉ số tài chính cho {B.symbol}.")
		return A
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('financial','kbs',Finance)