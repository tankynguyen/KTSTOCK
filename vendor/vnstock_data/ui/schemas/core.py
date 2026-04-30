'\nCore standardization logic for UI Reference Layer.\n'
from typing import Any,Dict
_SCHEMA_REGISTRY={}
_STANDARD_COLS_REGISTRY={}
_ENUM_REGISTRY={}
def register_schemas(schema_map,standard_cols,enum_map=None):
	'Register schema maps, standard columns, and optional enum value maps.';A=enum_map;_SCHEMA_REGISTRY.update(schema_map);_STANDARD_COLS_REGISTRY.update(standard_cols)
	if A:_ENUM_REGISTRY.update(A)
def standardize_columns(df,domain_method,source,strict=False,filter_unmapped=False):
	"\n    Standardize dataframe columns based on registered native schema mappings.\n    \n    Args:\n        df: Pandas DataFrame from provider.\n        domain_method: Key representing the domain method (e.g., 'company.profile').\n        source: Provider source (e.g., 'vci').\n        strict: If True, filters out any columns not part of the standard schema.\n        filter_unmapped: If True, filters out columns that aren't natively mapped or standard.\n    ";J='NFC';C=domain_method;A=df;import pandas as D,unicodedata as E
	if not isinstance(A,D.DataFrame):return A
	if A.empty:return A
	K=_SCHEMA_REGISTRY.get(C,{}).get(source)
	if K:
		F={E.normalize(J,str(A)):B for(A,B)in K.items()};N={A:F[E.normalize(J,str(A))]for A in A.columns if E.normalize(J,str(A))in F};A=A.rename(columns=N)
		if any(A.columns.duplicated()):
			L=[]
			for M in range(len(A.columns)):
				O=A.columns[M];G=A.iloc[:,M]
				if O not in['ticker','period']:G=D.to_numeric(G,errors='coerce')
				L.append(G)
			A=D.concat(L,axis=1);A=A.T.groupby(level=0).sum(min_count=1).T
		if filter_unmapped:B=_STANDARD_COLS_REGISTRY.get(C,[]);P=list(F.values());H=[A for A in A.columns if A in P or A in B];A=A[H]
	if strict:
		B=_STANDARD_COLS_REGISTRY.get(C,[])
		if B:H=[B for B in B if B in A.columns];A=A[H]
	for(I,Q)in _ENUM_REGISTRY.items():
		if I in A.columns:A[I]=A[I].replace(Q)
	return A