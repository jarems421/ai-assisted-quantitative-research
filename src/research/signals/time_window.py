"""Clean-room elapsed windows, inspired by chrono-ta; no thinning or parity claim."""
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
import math
from src.research.sec_pilot.provenance import instant

@dataclass(frozen=True)
class TimedObservation:
    at:datetime
    value:float
    def __post_init__(self):
        if self.at.tzinfo is None or self.at.utcoffset()!=timedelta(0) or not math.isfinite(self.value):raise ValueError('Aware UTC and finite value required')

class ElapsedWindow:
    def __init__(self,width:timedelta,bucket:timedelta,capacity=10000):
        if min(width.total_seconds(),bucket.total_seconds())<=0 or type(capacity) is not int or capacity<1:raise ValueError('Invalid duration/capacity')
        self.width=width;self.bucket=bucket;self.capacity=capacity;self.rows=[];self.last=None
    def push(self,observation):
        if not isinstance(observation,TimedObservation):raise TypeError('TimedObservation required')
        at=observation.at
        if self.last is not None and at<self.last:raise ValueError('Out-of-order timestamp')
        remaining=[r for r in self.rows if r.at>at-self.width]
        epoch=datetime(1970,1,1,tzinfo=timezone.utc)
        key=lambda t:(t-epoch)//self.bucket
        if remaining and key(remaining[-1].at)==key(at):remaining.pop()
        remaining.append(observation)
        if len(remaining)>self.capacity:raise ValueError('Capacity reached; never silently thin')
        self.rows=remaining;self.last=at
        return self.sma()
    def sma(self):return math.fsum(r.value for r in self.rows)/len(self.rows) if self.rows else None
    def value_ago(self,lag):
        if lag<timedelta(0) or not self.last:raise ValueError('Invalid lag/no observations')
        rows=[r for r in self.rows if r.at<=self.last-lag]
        return rows[-1].value if rows else None
    def roc(self,lag):
        old=self.value_ago(lag)
        return None if old in (None,0) else self.rows[-1].value/old-1
    def reset(self):self.rows=[];self.last=None
    def state(self):return {'version':1,'width_us':self.width//timedelta(microseconds=1),'bucket_us':self.bucket//timedelta(microseconds=1),'capacity':self.capacity,'rows':[(r.at.isoformat(),r.value) for r in self.rows]}
    @classmethod
    def restore(cls,state):
        if state['version']!=1:raise ValueError('Unknown state')
        obj=cls(timedelta(microseconds=state['width_us']),timedelta(microseconds=state['bucket_us']),state['capacity'])
        for at,value in state['rows']:obj.push(TimedObservation(instant(at),value))
        return obj
