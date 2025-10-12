# Heavenly Hosts Protocol (HHP) – Hardened MVP (Research Preview)

**Purpose:** Resonance-guided, address-free broadcast for cooperative LAN cells with minimal metadata exposure.
**Status:** Security-hardened research preview designed to withstand high-risk lab exercises and red-team evaluations.

## Quickstart (Developer Workstation, Python 3.11)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn hhp.api:app --host 127.0.0.1 --port 8080
```

Metrics are exposed under `GET /v1/metrics` and include fragment transmit/receive counters.

## Quickstart (Docker Compose, 3 Hardened Nodes)

```bash
docker compose up --build
# Metrics endpoints: http://localhost:8081/metrics, :8082, :8083
```

Each container derives an ephemeral QUIC certificate whose SHA-256 fingerprint is published via mDNS. Clients refuse any QUIC handshake that does not match the announced fingerprint, preventing opportunistic middleboxes from injecting themselves into the trust path.

## Security Hardening Highlights

- **Ephemeral identity binding:** Discovery beacons advertise a one-time token and the SHA-256 fingerprint of the node's transient QUIC certificate. Clients enforce this binding during TLS 1.3 handshakes to eliminate MITM opportunities while keeping identifiers short-lived.
- **Replay- and tamper-resilient fragments:** Constant 1024-byte fragments incorporate AEAD-encrypted payloads, per-fragment salts, and rolling anti-replay windows. Any deviation in size, fingerprint, or AEAD tag is dropped before resonance processing.
- **Cover-traffic with poisson timing:** Background transmissions continue to camouflage link activity. Cover payloads are indistinguishable from real fragments and share the same integrity enforcement pipeline.
- **Process-local metrics only:** Operational counters avoid leaking sensitive topic material while still supporting observability.

## Threat Model (Hardened MVP)
- **Adversaries:** Malicious LAN peers, active network injectors, and dedicated packet collectors.
- **Defenses:** XChaCha20-Poly1305 AEAD, HKDF-derived topic keys, constant-size (1024 B) fragments, Poisson cover-traffic, ephemeral discovery tokens, and QUIC certificate fingerprint pinning.
- **Out of scope:** Internet-scale P2P routing, nation-state global passive adversaries, large-scale Sybil or resource exhaustion campaigns.

Continue to treat the system as experimental: conduct threat-led testing before placing it in mission-critical environments, and rotate nodes frequently to maintain ephemerality.
