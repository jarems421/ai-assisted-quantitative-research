"""Entirely synthetic EXP999 SEC-style input; no real filing content."""
FIXTURE = {'accession': '0000000999-20-000001', 'issuer_cik': '0000000999', 'form': '10-K'}
SUBMISSION = b'''<SEC-DOCUMENT>0000000999-20-000001.txt
<SEC-HEADER>
<ACCEPTANCE-DATETIME>20200309183000
ACCESSION NUMBER: 0000000999-20-000001
CONFORMED SUBMISSION TYPE: 10-K
PUBLIC DOCUMENT COUNT: 1
CONFORMED PERIOD OF REPORT: 20191231
FILED AS OF DATE: 20200309
FILER:
\tCOMPANY DATA:
\t\tCOMPANY CONFORMED NAME: EXP999 Synthetic Issuer
\t\tCENTRAL INDEX KEY: 0000000999
</SEC-HEADER>
<DOCUMENT>
<TYPE>10-K
<SEQUENCE>1
<FILENAME>synthetic.htm
<TEXT><html><body>EXP999 only</body></html></TEXT>
</DOCUMENT>
</SEC-DOCUMENT>'''
INSTANCE = b'''<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:s="https://example.invalid/EXP999" xmlns:iso4217="http://www.xbrl.org/2003/iso4217">
<context id="flow"><entity><identifier scheme="http://www.sec.gov/CIK">0000000999</identifier></entity><period><startDate>2019-01-01</startDate><endDate>2019-12-31</endDate></period></context>
<context id="balance"><entity><identifier scheme="http://www.sec.gov/CIK">0000000999</identifier></entity><period><instant>2019-12-31</instant></period></context>
<unit id="USD"><measure>iso4217:USD</measure></unit>
<s:Revenue contextRef="flow" unitRef="USD" decimals="0">0</s:Revenue>
<s:Assets contextRef="balance" unitRef="USD" decimals="0">100</s:Assets>
</xbrl>'''
