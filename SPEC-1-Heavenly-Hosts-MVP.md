# SPEC-1-Heavenly-Hosts-MVP

## Background
Resonance-guided, address-free LAN broadcast with minimal observable metadata and strictly ephemeral identifiers. Objective: credible research baseline that can later expand into a P2P overlay.

## Requirements (MoSCoW)
- **MUST:** XChaCha20-Poly1305 AEAD, HKDF topic keys, 1024-byte constant fragments, replay protection, LAN discovery (mDNS), FastAPI control plane, cover-traffic enabled by default.
- **SHOULD:** QUIC datagram transport (aioquic), metrics endpoint, optional SQLite persistence.
- **COULD:** Desktop companion snippets, mobile readiness.
- **WON'T (MVP):** Internet-scale P2P routing, DHT/NAT traversal.

## Method (Summary)
- Packet header (ver/flags/pad_len/t_epoch/win_ctr/salt/nonce), AEAD with AAD = header + magic value.
- Deterministic hash-to-vector resonance embedding with θ = 0.85 acceptance threshold.
- DAG with TTL eviction, replay LRU cache, Poisson-distributed cover traffic.
- Discovery via mDNS/DNS-SD with ephemeral tokens; QUIC datagrams for transport.

## Implementation Plan (Staircase)
1. **M0 Scaffold:** Repository layout, Apache-2.0 license, pyproject, API skeleton.
2. **M1 Crypto & Packet:** HKDF, XChaCha, fragment builder (1024 B), unit tests passing.
3. **M2 Resonance & Replay:** `tag_vec`, cosine similarity, replay cache, tests passing.
4. **M3 Transport & Discovery:** aioquic datagrams, zeroconf peers, three-node compose exchanging fragments.
5. **M4 API & Metrics:** `/v1/inject`, `/v1/metrics`, end-to-end smoke test.
6. **M5 Docs:** README, threat model, quickstart guidance.

## Milestones
M0 through M5 as above, each with acceptance criteria (tests, end-to-end validation).

## Gathering Results
- Constant-size verification, cover-traffic rate, >90% acceptance at θ ≥ 0.85 during LAN testing.
- CPU < 50%, RAM < 200 MB per node in three-node compose scenario at 1k fragments/minute.

## Need Professional Help in Developing Your Architecture?
https://sammuti.com
