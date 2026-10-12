"""Offline text/decoded-character locator index; no semantic certification."""
from html.parser import HTMLParser
from html import unescape
import re
from src.research.spec import digest


class LocatedText(HTMLParser):
    def __init__(self,html):
        super().__init__(convert_charrefs=False); self.html=html; self.parts=[]; self.spans=[]; self.skip=0; self.skip_tag=None; self.length=0
        self.lines=[0]+[m.end() for m in re.finditer('\n',html)]; self.feed(html)
        self.text=''.join(self.parts)
    def handle_starttag(self,tag,attrs):
        if self.skip_tag:
            if tag==self.skip_tag:self.skip+=1
            return
        hidden=tag in ('script','style','ix:header','ix:hidden','xbrli:context','xbrli:unit') or re.search(r'display\s*:\s*none',dict(attrs).get('style',''),re.I)
        if hidden:self.skip=1;self.skip_tag=tag
    def handle_endtag(self,tag):
        if tag==self.skip_tag:
            self.skip-=1
            if not self.skip:self.skip_tag=None
    def handle_data(self,data):
        self.append_data(data,len(data))
    def handle_entityref(self,name):
        self.append_data(unescape('&'+name+';'),len(name)+2)
    def handle_charref(self,name):
        self.append_data(unescape('&#'+name+';'),len(name)+3)
    def append_data(self,data,source_length):
        if self.skip or not data.strip(): return
        line,col=self.getpos(); source=self.lines[line-1]+col
        value=' '.join(data.split())+' '
        self.spans.append((self.length,self.length+len(value),source,source+source_length))
        self.parts.append(value); self.length+=len(value)
    def locate(self,start,end):
        spans=[r for r in self.spans if r[0]<end and r[1]>start]
        if not spans: raise ValueError('No original text locator')
        return {'decoded_start':spans[0][2],'decoded_end':spans[-1][3],
                'normalized_start':start,'normalized_end':end,'normalized_span_sha256':digest(self.text[start:end]),
                'transform':'html_text_whitespace_v003; entity source lengths preserved; skip explicit hidden/header blocks; original UTF8 decoded spans, not byte offsets'}
    def hits(self,pattern,limit=8,before=200,after=700):
        return [self.locate(max(0,m.start()-before),min(len(self.text),m.end()+after)) for m in list(re.finditer(pattern,self.text,re.I))[:limit]]
