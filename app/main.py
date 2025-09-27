from fastapi import FastAPI
from app.models import InjectRequest, QueryRequest, MessageFragment
from app.cell import GabrielCell
from app.funnel_dag import FunnelDAG
from app.resonance import fragment_message, transmit_fragments
from app.storage import storage
from app.encryption import encrypt_message, decrypt_message, generate_keypair
from app.dissolution import dissolve
import logging, time

logging.basicConfig(
    filename="logs/events.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

app = FastAPI(
    title="Heavenly Hosts Protocol (Maximal)",
    description="Resonance-based ephemeral network with all layers",
    version="2.0.0"
)

dag = FunnelDAG()
keys = generate_keypair()

@app.post("/inject")
def inject_message(payload: InjectRequest):
    cell = GabrielCell(payload.signal_vector)
    node_id = dag.add_cell(cell, payload.timestamp, payload.semantic_tag)
    storage.add(node_id, cell)
    logging.info(f"Injected signal into DAG at node {node_id}")
    return {"status": "ok", "node_id": node_id}

@app.get("/query")
def query_resonance(payload: QueryRequest):
    results = dag.query(payload.signal_vector, payload.threshold)
    return {"status": "ok", "results": results}

@app.post("/transmit")
def transmit_message(msg: MessageFragment):
    encrypted = encrypt_message(keys["private"], keys["public"], msg.content)
    frags = fragment_message(encrypted, msg.fragment_size)
    recipients = transmit_fragments(dag, frags)
    return {"status": "ok", "recipients": recipients, "fragments": len(frags)}

@app.post("/dissolve")
def dissolve_nodes():
    removed = dissolve(dag, lifetime=60.0)
    return {"status": "ok", "removed": removed}
