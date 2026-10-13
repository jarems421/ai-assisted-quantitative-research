"""Versioned dispatch/redirect review on existing PilotHTTP; stages keep separate ceilings."""
import hashlib,json
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from src.research.procurement_pilot import PilotHTTP,contract
from src.research.phase3c.sources import SourceHTTP,put
from src.research.sec_pilot.acquisition import identity,now
from src.research.spec import digest

class BoundedHTTP(PilotHTTP):
    def __init__(self,root,provider,ceiling,*,transport=None,sleep=None):
        if provider not in ('CONGRESS','SEC','HOUSE','SENATE') or ceiling not in (24,32):raise ValueError('Unknown authorized stage/provider')
        self.global_root=Path(root);self.provider=provider;self.locations={};self.reviewed=[]
        def wrapped(url,headers,payload):
            if urlsplit(url).hostname=='www.sec.gov':headers=dict(headers,**{'User-Agent':identity()})
            status,h,b,final=(transport or SourceHTTP._transport)(url,headers,payload)
            location=next((v for k,v in h.items() if k.lower()=='location'),None)
            if location:
                self.locations[url]=urljoin(url,location)
                record={'url':url,'location':self.locations[url],'status':status,'body_sha256':hashlib.sha256(b).hexdigest(),'received_at':now()}
                put(self.global_root/provider/'redirect_headers'/(digest(record)+'.json'),record)
            return status,h,b,final
        kwargs={'transport':wrapped}
        if sleep is not None:kwargs['sleep']=sleep
        super().__init__(contract(),root=self.global_root/provider,**kwargs)
        self.m={'version':'integration_dispatch_v002','request_ceiling':ceiling,'retry':contract()['retry'],'provider':provider}
        self.allowed=set()
        reviews=[json.loads(p.read_bytes()) for p in (self.root/'redirect_reviews').glob('*.json')]
        if reviews:
            latest=max(reviews,key=lambda r:r['reviewed_at_utc']);self.review_errors=latest['errors'];self.review_stop_hash=latest['stop_sha256'];self.reviewed=[latest['target']]
    def starts(self):return sorted(self.global_root.glob('*/reservations/*.json'))
    def allow(self,url,purpose):
        p=urlsplit(url);hosts={'CONGRESS':{'huggingface.co','cdn-lfs.huggingface.co','cas-bridge.xethub.hf.co'},'SEC':{'www.sec.gov'},'HOUSE':{'disclosures-clerk.house.gov'},'SENATE':{'efdsearch.senate.gov'}}[self.provider]
        if p.scheme!='https' or p.hostname not in hosts or p.username or p.password:raise ValueError('Source host/scheme outside reviewed contract')
        receipt={'url':url,'purpose':purpose,'provider':self.provider,'ceiling':self.m['request_ceiling'],'frozen_at_utc':now(),'performance_authorized':False}
        put(self.root/'dispatch'/(digest(receipt)+'.json'),receipt);self.allowed.add(url)
        if self.reviewed and self.reviewed_stop_allows(self.reviewed[-1]):self.reviewed.append(url)
    def reviewed_stop_allows(self,url):
        if url not in self.reviewed:return False
        receipts=[json.loads(p.read_bytes()) for p in (self.root/'receipts').glob('*.json')]
        if any(r['status'] not in (200,301,302,303,307,308) for r in receipts) or list((self.root/'stops').glob('*.json')):return False
        errors={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.root/'errors').glob('*.json')}
        return errors==self.review_errors and hashlib.sha256((self.root/'publication_stop.json').read_bytes()).hexdigest()==self.review_stop_hash
    def fetch_reviewed(self,url,purpose):
        self.allow(url,purpose)
        for hop in range(4):
            try:return self.fetch(url,purpose=purpose)
            except ValueError:
                target=self.locations.get(url)
                receipts=[json.loads(p.read_bytes()) for p in (self.root/'receipts').glob('*.json')]
                source=sorted([r for r in receipts if r['url']==url],key=lambda r:r['request_started_at_utc'])
                if not target or not source or source[-1]['status'] not in (301,302,303,307,308) or hop==3:raise
                # Explicit exact target freeze/review before next hop; originals/stops never removed.
                self.allow(target,'REVIEWED_PUBLISHER_REDIRECT_'+purpose)
                self.review_errors={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.root/'errors').glob('*.json')}
                self.review_stop_hash=hashlib.sha256((self.root/'publication_stop.json').read_bytes()).hexdigest()
                self.reviewed.append(target)
                review={'from_receipt_sha256':digest(source[-1]),'target':target,'stop_sha256':self.review_stop_hash,'errors':self.review_errors,'reason':'Publisher-declared redirect only, no denial override','reviewed_at_utc':now()}
                put(self.root/'redirect_reviews'/(digest(review)+'.json'),review);url=target
        raise ValueError('Redirect hop ceiling reached')
