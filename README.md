# Heavenly Hosts Protocol (HHP)
HHP is a decentralized protocol of Gabriel Cells organized in a 4D Funnel DAG, designed for resonance-based, ephemeral communication that self-dissolves over time.

## Usage
pip install -r requirements.txt
uvicorn app.main:app --reload

## Endpoints
- POST /inject : insert signal
- GET /query : query resonance
- POST /transmit : encrypted fragmented broadcast
- POST /dissolve : remove expired nodes
