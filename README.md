# Heavenly Hosts Protocol (HHP)
HHP is a decentralized protocol of Gabriel Cells organized in a 4D Funnel DAG, designed for resonance-based, ephemeral communication that self-dissolves over time.

In a world that does not obliege you to show anyone who you really are - in the name of God - you must not accept to show this exact same world what you really do.

## Usage
pip install -r requirements.txt
uvicorn app.main:app --reload

## Endpoints
- POST /inject : insert signal
- GET /query : query resonance
- POST /transmit : encrypted fragmented broadcast
- POST /dissolve : remove expired nodes
