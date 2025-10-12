import time
from collections import OrderedDict

class ReplayCache:
    def __init__(self, max_entries:int=100_000, ttl_sec:int=600):
        self.max = max_entries; self.ttl = ttl_sec
        self._d: OrderedDict[tuple, float] = OrderedDict()

    def seen(self, t_epoch:int, win_ctr:int, nonce:bytes)->bool:
        key=(t_epoch, win_ctr, nonce)
        now=time.time()
        if key in self._d: return True
        self._d[key]=now
        self._trim(now); return False

    def _trim(self, now:float):
        # TTL-basiert + LRU
        for k,t in list(self._d.items()):
            if now - t > self.ttl: self._d.pop(k, None)
        while len(self._d)>self.max:
            self._d.popitem(last=False)
