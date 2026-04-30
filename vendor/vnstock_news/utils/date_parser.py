import re
from datetime import datetime,timedelta
def normalize_datetime(time_str):
	'\n    Chuẩn hoá các định dạng thời gian thành ISO YYYY-MM-DD HH:MM:SS.\n    Xử lý được các dạng:\n    - Relative: "1 giờ trước", "5 phút trước", "hôm qua".\n    - Raw: "19/03/2024 09:11", "2026-04-02 13:49", "Thứ năm, 02/04/2026 - 13:49"\n    ';G='(\\d+)';D='%Y-%m-%d %H:%M:%S';A=time_str
	if not A:return''
	A=A.strip().lower();E=datetime.now()
	if'trước'in A or'vừa xong'in A:
		if'phút'in A:
			B=re.search(G,A)
			if B:C=E-timedelta(minutes=int(B.group(1)));return C.strftime(D)
		elif'giờ'in A or'tiếng'in A:
			B=re.search(G,A)
			if B:C=E-timedelta(hours=int(B.group(1)));return C.strftime(D)
		elif'ngày'in A:
			B=re.search(G,A)
			if B:C=E-timedelta(days=int(B.group(1)));return C.strftime(D)
		return E.strftime(D)
	if'hôm qua'in A:C=E-timedelta(days=1);return C.strftime(D)
	F=re.sub('^(thứ\\s\\S+,\\s*)','',A,flags=re.IGNORECASE);F=F.replace(' - ',' ');M=['(\\d{1,2})[/-](\\d{1,2})[/-](\\d{4})\\s+(\\d{1,2}):(\\d{1,2})','(\\d{4})[/-](\\d{1,2})[/-](\\d{1,2})[\\sT]+(\\d{1,2}):(\\d{1,2})']
	for N in M:
		B=re.search(N,F)
		if B:
			if len(B.group(3))==4:H,I,J,K,L=B.groups()
			else:J,I,H,K,L=B.groups()
			try:C=datetime(int(J),int(I),int(H),int(K),int(L));return C.strftime(D)
			except ValueError:pass
	return A