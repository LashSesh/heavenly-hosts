from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_inject_and_query():
    payload = {
        "signal_vector": [0.1, 0.2, 0.3, 0.4],
        "timestamp": 12345.6,
        "semantic_tag": "test",
    }
    res = client.post("/inject", json=payload)
    assert res.status_code == 200
