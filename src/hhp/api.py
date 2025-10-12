from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Set

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import config, resonance
from .dag import DAG
from .replay import ReplayCache
from .transport import HHPTransport

app = FastAPI(title="HHP Control API", version="1.0")

_CFG_PATH = os.environ.get("HHP_CONFIG")
if _CFG_PATH and Path(_CFG_PATH).exists():
    CFG = config.load(Path(_CFG_PATH))
else:
    CFG = config.Cfg()

DAG_STORE = DAG()
REPLAY = ReplayCache(max_entries=CFG.crypto.max_replay_entries, ttl_sec=CFG.crypto.replay_window_ttl)
METRICS = {"fragments_tx": 0, "fragments_rx": 0}
KNOWN_TAGS: Set[str] = set()
_TAG_LOCK = asyncio.Lock()
TRANSPORT = HHPTransport(cfg=CFG, dag=DAG_STORE, replay=REPLAY, metrics=METRICS, known_tags=KNOWN_TAGS)


class InjectIn(BaseModel):
    semantic_tag: str
    payload: bytes


class TransmitIn(BaseModel):
    semantic_tag: str
    payload: bytes


class DissolveIn(BaseModel):
    older_than_secs: int = 900


@app.on_event("startup")
async def _startup() -> None:
    await TRANSPORT.start()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await TRANSPORT.stop()


@app.post("/v1/inject")
async def inject(req: InjectIn):
    vec = resonance.tag_vec(req.semantic_tag)
    cell_id = DAG_STORE.insert_cell(vec.tobytes())
    async with _TAG_LOCK:
        KNOWN_TAGS.add(req.semantic_tag)
    return {"cell_id": cell_id}


@app.post("/v1/transmit")
async def transmit(req: TransmitIn):
    async with _TAG_LOCK:
        KNOWN_TAGS.add(req.semantic_tag)
    await TRANSPORT.transmit(req.semantic_tag, req.payload)
    return {"fragments_tx": METRICS["fragments_tx"]}


@app.post("/v1/dissolve")
async def dissolve(req: DissolveIn):
    if req.older_than_secs <= 0:
        raise HTTPException(status_code=400, detail="older_than_secs must be positive")
    DAG_STORE.dissolve(req.older_than_secs)
    return {"remaining": len(DAG_STORE.nodes)}


@app.get("/v1/metrics")
async def metrics():
    return METRICS

