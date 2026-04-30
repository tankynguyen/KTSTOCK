'\nModule quản lý thông tin công ty từ nguồn dữ liệu VCI.\n'
_f='object'
_e='is_event'
_d='affiliates'
_c='working'
_b='quantity'
_a='owner_name'
_Z='owner_code'
_Y='detailed'
_X='public_date'
_W='first'
_V='content'
_U='ownership_percent'
_T='position_name'
_S='owner_type'
_R='ms'
_Q='organ_name'
_P='all'
_O='ticker'
_N='percentage'
_M='%Y-%m-%d'
_L='profile'
_K='sector'
_J='%Y%m%d'
_I='en_'
_H='organ_code'
_G='data'
_F='GET'
_E='__typename'
_D='update_date'
_C='VCI.ext'
_B='symbol'
_A=None
import json,pandas as pd
from typing import Dict,Optional,Union,List
from datetime import datetime,timedelta
from vnstock.core.utils.logger import get_logger
from vnstock.core.utils.transform import clean_html_dict,flatten_dict_to_df,flatten_list_to_df,reorder_cols,drop_cols_by_pattern
from vnstock_data.core.utils.client import send_request
from vnstock_data.core.utils.user_agent import get_headers
from vnstock.core.utils.parser import get_asset_type,camel_to_snake
from vnai import agg_execution
from vnstock_data.explorer.vci.const import _VCIQ_URL,_VCI_COMPANY_URL
logger=get_logger(__name__)
class Company:
	'\n    Class (lớp) quản lý các thông tin liên quan đến công ty từ nguồn dữ liệu VCI.\n\n    Tham số:\n        - symbol (str): Mã chứng khoán của công ty cần truy xuất thông tin.\n        - random_agent (bool): Sử dụng user-agent ngẫu nhiên hoặc không. Mặc định là False.\n        - to_df (bool): Chuyển đổi dữ liệu thành DataFrame hoặc không. Mặc định là True.\n        - show_log (bool): Hiển thị thông tin log hoặc không. Mặc định là False.\n    '
	def __init__(A,symbol,random_agent=False,to_df=True,show_log=False):
		'\n        Khởi tạo đối tượng Company với các tham số cho việc truy xuất dữ liệu.\n        ';B=show_log;A.symbol=symbol.upper();A.asset_type=get_asset_type(A.symbol)
		if A.asset_type not in['stock']:raise ValueError('Mã chứng khoán không hợp lệ. Chỉ cổ phiếu mới có thông tin.')
		A.headers=get_headers(data_source='VCI',random_agent=random_agent);A.show_log=B;A.to_df=to_df;A.base_url=_VCI_COMPANY_URL;A.cms_base_url='https://www.vietcap.com.vn/api/cms-service/v2'
		if not B:logger.setLevel('CRITICAL')
	def _fetch_company_details(A):
		'\n        Fetch company overview details from REST API.\n        \n        Returns:\n            Dict: Company details data.\n        ';B=f"{A.base_url}/details?ticker={A.symbol}"
		if A.show_log:logger.debug(f"Requesting company details for {A.symbol} from {B}")
		C=send_request(url=B,headers=A.headers,method=_F,show_log=A.show_log);return C.get(_G,{})
	def _fetch_shareholders(A):
		'\n        Fetch shareholder structure from REST API.\n        \n        Returns:\n            Dict: Shareholder data.\n        ';B=f"{A.base_url}/{A.symbol}/shareholder-structure"
		if A.show_log:logger.debug(f"Requesting shareholder structure for {A.symbol} from {B}")
		C=send_request(url=B,headers=A.headers,method=_F,show_log=A.show_log);return C.get(_G,{})
	def _fetch_shareholder_list(A):
		'\n        Fetch shareholder list from REST API (includes both individuals and organizations).\n        \n        Returns:\n            Dict: Shareholder list data.\n        ';B=f"{A.base_url}/{A.symbol}/shareholder"
		if A.show_log:logger.debug(f"Requesting shareholder list for {A.symbol} from {B}")
		C=send_request(url=B,headers=A.headers,method=_F,show_log=A.show_log);return C.get(_G,[])
	def _fetch_relationships(A):
		'\n        Fetch subsidiary and affiliate relationships from REST API.\n        \n        Returns:\n            Dict: Relationship data.\n        ';B=f"{A.base_url}/{A.symbol}/relationship"
		if A.show_log:logger.debug(f"Requesting relationships for {A.symbol} from {B}")
		C=send_request(url=B,headers=A.headers,method=_F,show_log=A.show_log);return C.get(_G,{})
	def _fetch_news_events(A,from_date=_A,to_date=_A,event_codes=_A):
		'\n        Fetch news and events from REST API.\n        \n        Returns:\n            List: News and events data.\n        ';D=event_codes;C=to_date;B=from_date
		if B is _A:B=(datetime.now()-timedelta(days=120)).strftime(_J)
		if C is _A:C=datetime.now().strftime(_J)
		if D is _A:D='DIV,ISS'
		E=f"{_VCIQ_URL}/v1/news-events-for-chart?ticker={A.symbol}&fromDate={B}&toDate={C}&languageId=1&eventCode={D}"
		if A.show_log:logger.debug(f"Requesting news and events for {A.symbol} from {E}")
		F=send_request(url=E,headers=A.headers,method=_F,show_log=A.show_log);return F.get(_G,[])
	def _fetch_news(A,from_date=_A,to_date=_A,page=0,size=50):
		'\n        Fetch news from REST API (alternative endpoint with more data).\n        \n        Returns:\n            List: News data.\n        ';C=to_date;B=from_date
		if B is _A:B=(datetime.now()-timedelta(days=3650)).strftime(_J)
		if C is _A:C=datetime.now().strftime(_J)
		D=f"{_VCIQ_URL}/v1/news?ticker={A.symbol}&fromDate={B}&toDate={C}&languageId=1&page={page}&size={size}"
		if A.show_log:logger.debug(f"Requesting news for {A.symbol} from {D}")
		F=send_request(url=D,headers=A.headers,method=_F,show_log=A.show_log);E=F.get(_G,{})
		if isinstance(E,dict):return E.get(_V,[])
		return[]
	def _fetch_financial_statistics(A):
		'\n        Fetch financial statistics summary from REST API.\n        \n        Returns:\n            Dict: Financial statistics data.\n        ';B=f"{A.base_url}/{A.symbol}/statistics-financial"
		if A.show_log:logger.debug(f"Requesting financial statistics for {A.symbol} from {B}")
		C=send_request(url=B,headers=A.headers,method=_F,show_log=A.show_log);return C.get(_G,{})
	def _fetch_analysis_reports(A,company_id=_A):
		'\n        Fetch analysis reports from CMS API.\n        \n        Args:\n            company_id (str): Company ID for the CMS API. If None, will try to fetch from company details.\n        \n        Returns:\n            List: Analysis reports data.\n        ';F='133';B=company_id
		if B is _A:
			try:G=A._fetch_company_details();B=G.get('id',F)
			except:B=F
		C=f"{A.cms_base_url}/page/analysis?is-all=false&page=0&size=20&direction=DESC&sortBy=date&companyId={B}&page-ids=144&page-ids=141&language=1"
		if A.show_log:logger.debug(f"Requesting analysis reports from {C}")
		H=send_request(url=C,headers=A.headers,method=_F,show_log=A.show_log);D=H.get(_G,{})
		if isinstance(D,dict):
			E=D.get('pagingGeneralResponses',{})
			if isinstance(E,dict):return E.get(_V,[])
		return[]
	@agg_execution(_C)
	def info(self):
		'\n        Truy xuất thông tin công ty theo chuẩn schema mapping.\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa thông tin công ty với columns chuẩn hóa.\n        ';N='listing_date';M='listingDate';L='enProfile';K='sectorVn';J='enOrganShortName';I='viOrganShortName';H='enOrganName';G='viOrganName';E='short_name';D='name';F=self._fetch_company_details()
		if not F:return pd.DataFrame()
		A=pd.DataFrame([F]);B={}
		if _O in A.columns:B[_B]=A[_O].iloc[0]
		if G in A.columns:B[D]=A[G].iloc[0]
		elif H in A.columns:B[D]=A[H].iloc[0]
		if I in A.columns:B[E]=A[I].iloc[0]
		elif J in A.columns:B[E]=A[J].iloc[0]
		if K in A.columns:B[_K]=A[K].iloc[0]
		elif _K in A.columns:B[_K]=A[_K].iloc[0]
		if _L in A.columns:B[_L]=A[_L].iloc[0]
		elif L in A.columns:B[_L]=A[L].iloc[0]
		if M in A.columns:B[N]=A[M].iloc[0]
		C=pd.DataFrame([B]);O=[_B,D,E,_K,_L,N];P=[A for A in O if A in C.columns];C=C[P];return C
	@agg_execution(_C)
	def overview(self):
		'\n        Truy xuất thông tin tổng quan của công ty (raw data từ API).\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa thông tin tổng quan của công ty.\n        ';E='sector_vn';B='company_profile';C=self._fetch_company_details()
		if not C:return pd.DataFrame()
		A=pd.DataFrame([C]);A.columns=[camel_to_snake(A)for A in A.columns];A=drop_cols_by_pattern(A,[_I,'__'])
		if E in A.columns and _K in A.columns:A=A.drop(columns=[E])
		F={'vi_organ_name':_Q,'vi_organ_short_name':'organ_short_name',_L:B,'number_of_shares_mkt_cap':'issue_share',_O:_B};D={B:C for(B,C)in F.items()if B in A.columns}
		if D:A=A.rename(columns=D)
		if B in A.columns:
			import re
			def G(text):
				A=text
				if not isinstance(A,str):return A
				A=re.sub('<[^>]+>','',A);import html;A=html.unescape(A);A=' '.join(A.split());return A
			A[B]=A[B].apply(G)
		A=reorder_cols(A,[_B],position=_W);return A
	@agg_execution(_C)
	def shareholders(self,mode=_Y):
		"\n        Truy xuất thông tin cổ đông của công ty.\n        \n        Tham số:\n            - mode (str): Chế độ hiển thị\n                - 'summary': Tóm tắt cơ cấu cổ đông (mặc định)\n                - 'detailed': Danh sách chi tiết tất cả cổ đông\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa thông tin cổ đông của công ty.\n        ";I='owner_full_name';G='share_own_percent';F='share_holder';E=mode;D=self
		if E=='summary':
			B=D._fetch_shareholders()
			if not B:return pd.DataFrame()
			A=pd.DataFrame(B)if isinstance(B,list)else pd.DataFrame([B]);A.columns=[camel_to_snake(A)for A in A.columns];A=drop_cols_by_pattern(A,[_E,_O,_I])
			if _D in A.columns and A[_D].dtype in[int,float]:A[_D]=pd.to_datetime(A[_D],unit=_R).dt.strftime(_M)
			C={}
			if I in A.columns:C[I]=F
			if _N in A.columns:C[_N]=G
			if C:A=A.rename(columns=C)
			return A
		elif E==_Y:
			B=D._fetch_shareholder_list()
			if not B:return pd.DataFrame()
			A=pd.DataFrame(B);A.columns=[camel_to_snake(A)for A in A.columns];A=drop_cols_by_pattern(A,[_E,_O,_I,_S,_Z,_T,_X]);C={_a:F,_N:G};H={B:C for(B,C)in C.items()if B in A.columns}
			if H:A=A.rename(columns=H)
			A.insert(0,_B,D.symbol);J=[_B,F,_b,G,_D];K=[B for B in J if B in A.columns];A=A[K];return A
		else:raise ValueError(f"Invalid mode: {E}. Use 'summary' or 'detailed'")
	@agg_execution(_C)
	def officers(self,filter_by=_c):
		"\n        Truy xuất thông tin lãnh đạo công ty (cá nhân có vị trí).\n\n        Tham số:\n            - filter_by (str): Lọc lãnh đạo đang làm việc hoặc đã từ nhiệm hoặc tất cả.\n                - 'working': Lọc lãnh đạo đang làm việc (mặc định).\n                - 'resigned': Lọc lãnh đạo đã từ nhiệm.\n                - 'all': Lọc tất cả lãnh đạo.\n\n        Returns:\n            pd.DataFrame: DataFrame chứa thông tin lãnh đạo của công ty.\n        ";G='officer_own_quantity';F='officer_own_percent';E='officer_position';D='officer_name'
		if filter_by not in[_c,'resigned',_P]:raise ValueError("filter_by chỉ nhận giá trị 'working' hoặc 'resigned' hoặc 'all'")
		B=self._fetch_shareholder_list()
		if not B:return pd.DataFrame()
		A=pd.DataFrame(B)if isinstance(B,list)else pd.DataFrame([B]);A.columns=[camel_to_snake(A)for A in A.columns]
		if _S in A.columns:A=A[A[_S]=='INDIVIDUAL']
		if _T in A.columns:A=A[A[_T].notna()]
		A=drop_cols_by_pattern(A,[_I,'__',_Z,_S,_X]);H={_a:D,_T:E,_N:F,_b:G};C={B:C for(B,C)in H.items()if B in A.columns}
		if C:A=A.rename(columns=C)
		A.insert(0,_B,self.symbol)
		if _D in A.columns and A[_D].dtype in[int,float]:A[_D]=pd.to_datetime(A[_D],unit=_R).dt.strftime(_M)
		I=[_B,D,E,F,G,_D];J=[B for B in I if B in A.columns];A=A[J];return A
	@agg_execution(_C)
	def subsidiaries(self,filter_by=_P):
		"\n        Truy xuất thông tin công ty con của công ty.\n\n        Tham số:\n            - filter_by (str): Lọc công ty con hoặc công ty liên kết.\n                - 'all': Lọc tất cả.\n                - 'subsidiary': Lọc công ty con.\n                - 'affiliate': Lọc công ty liên kết.\n\n        Returns:\n            pd.DataFrame: DataFrame chứa thông tin công ty con.\n        ";Q='owned_percentage';P='right_organ_code';O='right_organ_name_vi';N='affiliate';M='subsidiary';L='sub_organ_code';H=filter_by;G=self
		if H not in[_P,M,N]:raise ValueError("filter_by chỉ nhận giá trị 'all' hoặc 'subsidiary' hoặc 'affiliate'")
		D=G._fetch_relationships()
		if not D:return pd.DataFrame()
		if isinstance(D,dict):I=D.get('subsidiaries',[]);J=D.get(_d,[])
		else:I=[];J=[]
		E=[]
		if H in[_P,M]and I:
			A=pd.DataFrame(I);A.columns=[camel_to_snake(A)for A in A.columns];A=drop_cols_by_pattern(A,[_E,_I]);K={O:_Q,P:L,Q:_U};C={B:C for(B,C)in K.items()if B in A.columns}
			if C:A=A.rename(columns=C)
			if _H in A.columns:A=A.drop(columns=[_H])
			A.insert(0,_B,G.symbol);E.append(A)
		if H in[_P,N]and J:
			B=pd.DataFrame(J);B.columns=[camel_to_snake(A)for A in B.columns];B=drop_cols_by_pattern(B,[_E,_I]);K={O:_Q,P:L,Q:_U};C={A:C for(A,C)in K.items()if A in B.columns}
			if C:B=B.rename(columns=C)
			if _H in B.columns:B=B.drop(columns=[_H])
			B.insert(0,_B,G.symbol);E.append(B)
		if E:F=pd.concat(E,ignore_index=True);R=[_B,_Q,_U,L,'type'];S=[A for A in R if A in F.columns];F=F[S];return F
		else:return pd.DataFrame()
	@agg_execution(_C)
	def affiliate(self):
		'\n        Truy xuất thông tin công ty liên kết của công ty.\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa thông tin công ty liên kết.\n        ';B=self._fetch_relationships()
		if not B:return pd.DataFrame()
		if isinstance(B,dict):C=B.get(_d,[])
		else:C=[]
		if not C:return pd.DataFrame()
		A=pd.DataFrame(C);A.columns=[camel_to_snake(A)for A in A.columns];A=drop_cols_by_pattern(A,[_I,_E])
		if _H in A.columns:A=A.drop(columns=[_H])
		if _N in A.columns:A=A.rename(columns={_N:_U})
		return A
	@agg_execution(_C)
	def news(self):
		'\n        Truy xuất tin tức liên quan đến công ty.\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa tin tức liên quan đến công ty.\n        ';B=self._fetch_news()
		if not B:return pd.DataFrame()
		A=pd.DataFrame(B);A.columns=[camel_to_snake(A)for A in A.columns];C=[B for B in[_H,_B,_E,_e,'event','create_by','update_by','status','create_date',_D,'source_code','expert_id','is_tranfer']if B in A.columns]
		if C:A=A.drop(columns=C)
		return A
	def _fetch_events(A,event_codes=_A,from_date=_A,to_date=_A,page=0,size=50):
		"\n        Fetch events from REST API.\n        \n        Args:\n            event_codes (str): Event codes to fetch (comma-separated)\n                - 'DIV,ISS': Trả cổ tức & phát hành thêm\n                - 'DDIND,DDINS,DDRP': Giao dịch cổ đông lớn & cổ đông nội bộ\n                - 'AGME,AGMR,EGME': Đại hội cổ đông\n                - 'AIS,MA,MOVE,NLIS,OTHE,RETU,SUSP': Sự kiện khác\n            from_date (str): Start date in YYYYMMDD format\n            to_date (str): End date in YYYYMMDD format\n            page (int): Page number (0-indexed)\n            size (int): Number of items per page\n        \n        Returns:\n            List: Events data.\n        ";D=to_date;C=from_date;B=event_codes
		if B is _A:B='DIV,ISS,DDIND,DDINS,DDRP,AGME,AGMR,EGME,AIS,MA,MOVE,NLIS,OTHE,RETU,SUSP'
		if C is _A:C=(datetime.now()-timedelta(days=3650)).strftime(_J)
		if D is _A:D=datetime.now().strftime(_J)
		E=f"{_VCIQ_URL}/v1/events?ticker={A.symbol}&fromDate={C}&toDate={D}&eventCode={B}&page={page}&size={size}"
		if A.show_log:logger.debug(f"Requesting events for {A.symbol} from {E}")
		G=send_request(url=E,headers=A.headers,method=_F,show_log=A.show_log);F=G.get(_G,{})
		if isinstance(F,dict):return F.get(_V,[])
		return[]
	@agg_execution(_C)
	def events(self):
		'\n        Truy xuất các sự kiện của công ty.\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa các sự kiện của công ty.\n        ';C=self._fetch_events()
		if not C:return pd.DataFrame()
		A=pd.DataFrame(C);A.columns=[camel_to_snake(A)for A in A.columns];D=[B for B in[_H,_B,_E,_e,'event','organ_name_en','organ_name_vi']if B in A.columns]
		if D:A=A.drop(columns=D)
		E=[_X,'issue_date','record_date','exright_date','display_date']
		for B in E:
			if B in A.columns:
				if A[B].dtype in[int,float]:A[B]=pd.to_datetime(A[B],unit=_R).dt.strftime(_M)
				elif A[B].dtype==_f:
					try:A[B]=pd.to_datetime(A[B]).dt.strftime(_M)
					except:pass
		return A
	@agg_execution(_C)
	def reports(self):
		'\n        Truy xuất báo cáo phân tích về công ty.\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa các báo cáo phân tích về công ty.\n        ';B='date';C=self._fetch_analysis_reports()
		if not C:return pd.DataFrame()
		A=pd.DataFrame(C);A.columns=[camel_to_snake(A)for A in A.columns];D=[B for B in[_E,'page_id']if B in A.columns]
		if D:A=A.drop(columns=D)
		if B in A.columns:
			if A[B].dtype in[int,float]:A[B]=pd.to_datetime(A[B],unit=_R).dt.strftime(_M)
			elif A[B].dtype==_f:
				try:A[B]=pd.to_datetime(A[B]).dt.strftime(_M)
				except:pass
		return A
	@agg_execution(_C)
	def trading_stats(self):
		'\n        Truy xuất thống kê giao dịch của công ty.\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa thống kê giao dịch của công ty.\n        ';B=self._fetch_company_details()
		if not B:return pd.DataFrame()
		A=pd.DataFrame([B]);A.columns=[camel_to_snake(A)for A in A.columns];A=drop_cols_by_pattern(A,[_E]);A[_B]=self.symbol;A=reorder_cols(A,[_B],position=_W);return A
	@agg_execution(_C)
	def ratio_summary(self):
		'\n        Truy xuất tóm tắt các tỷ lệ tài chính của công ty.\n        \n        Returns:\n            pd.DataFrame: DataFrame chứa tóm tắt các tỷ lệ tài chính của công ty.\n        ';B=self._fetch_financial_statistics()
		if not B:return pd.DataFrame()
		if isinstance(B,list):
			if len(B)==0:return pd.DataFrame()
			A=pd.DataFrame(B)
		else:A=pd.DataFrame([B])
		A.columns=[camel_to_snake(str(A))for A in A.columns];A=drop_cols_by_pattern(A,[_E]);A[_B]=self.symbol;A=reorder_cols(A,cols=[_B],position=_W);return A
from vnstock_data.core.registry import ProviderRegistry
ProviderRegistry.register('company','vci',Company)