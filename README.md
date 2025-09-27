# Heavenly Hosts Protocol
Full Python implementation of the Heavenly Hosts Protocol (HHP) including:
- Gabriel Cells
- 4D Funnel DAG
- Resonance-based fragmented communication
- Ephemeral dissolution layer
- Encryption using NaCl
- Logging and visualization

## Usage
pip install -r requirements.txt
uvicorn app.main:app --reload

## Endpoints
- POST /inject : insert signal
- GET /query : query resonance
- POST /transmit : encrypted fragmented broadcast
- POST /dissolve : remove expired nodes
