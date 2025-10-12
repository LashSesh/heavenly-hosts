import time, uuid
from dataclasses import dataclass

@dataclass
class Cell:
    id:str
    vec:bytes
    created_at:float
    ttl_sec:int=900

class DAG:
    def __init__(self): self.nodes:dict[str,Cell]={}
    def insert_cell(self, vec:bytes, ttl_sec:int=900)->str:
        cid=str(uuid.uuid4()); self.nodes[cid]=Cell(cid, vec, time.time(), ttl_sec); return cid
    def dissolve(self, older_than_secs:int):
        now=time.time()
        for k, c in list(self.nodes.items()):
            if now - c.created_at > older_than_secs: self.nodes.pop(k, None)
