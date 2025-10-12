# Heavenly Hosts Protocol (HHP) – MVP (Research Preview)

**Purpose:** Resonanz-basierter, adressenloser Broadcast mit minimalen Metadaten.
**Status:** Experimentell. Nicht für Hochrisiko-Anwendungen geeignet.

## Quickstart (Dev, Python 3.11)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn hhp.api:app --host 127.0.0.1 --port 8080
```

## Quickstart (Docker Compose, 3 Nodes)

```bash
docker compose up --build
# Metriken: http://localhost:8081/metrics etc.
```

## Threat Model (MVP)
- Gegner: LAN-Sniffer, bösartiger Peer.
- Schutz: XChaCha20-Poly1305 AEAD, HKDF Topic-Keys, konstante Fragmentgröße (1024B),
  Poisson Cover Traffic, keine stabilen IDs.
- Nicht gedeckt: Globaler passiver Gegner, Internet-P2P, Sybil/DoS im großen Stil.
