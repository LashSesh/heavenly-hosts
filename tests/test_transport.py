import asyncio

from hhp import config
from hhp.dag import DAG
from hhp.replay import ReplayCache
from hhp.transport import HHPTransport


def test_process_fragment_stores_payload():
    cfg = config.Cfg()
    dag = DAG()
    metrics = {"fragments_tx": 0, "fragments_rx": 0}
    known_tags = {"alpha"}
    transport = HHPTransport(cfg=cfg, dag=dag, replay=ReplayCache(), metrics=metrics, known_tags=known_tags)

    payload = b"secret-payload"
    fragment = transport._build_fragment("alpha", payload, cover=False)

    asyncio.run(transport.process_fragment(fragment))

    assert any(cell.payload == payload for cell in dag.nodes.values())
    assert metrics["fragments_rx"] == 1


def test_process_fragment_skips_cover_payload_storage():
    cfg = config.Cfg()
    dag = DAG()
    metrics = {"fragments_tx": 0, "fragments_rx": 0}
    known_tags = {"beta"}
    transport = HHPTransport(cfg=cfg, dag=dag, replay=ReplayCache(), metrics=metrics, known_tags=known_tags)

    payload = b"cover-payload"
    fragment = transport._build_fragment("beta", payload, cover=True)

    asyncio.run(transport.process_fragment(fragment))

    assert all(cell.payload != payload for cell in dag.nodes.values())
    assert metrics["fragments_rx"] == 1
