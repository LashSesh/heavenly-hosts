# SPEC-1-Heavenly-Hosts-MVP

## Background
Resonanz-basierter, adressenloser Broadcast (LAN), minimal sichtbare Metadaten, Ephemerität. Ziel: seriöse Forschungsbasis, später P2P-Overlay.

## Requirements (MoSCoW)
- MUST: XChaCha20-Poly1305 AEAD, HKDF Topic-Keys, 1024B konstante Fragmente, Replay-Schutz, LAN-Discovery (mDNS), Control-API (FastAPI), Cover-Traffic an.
- SHOULD: QUIC Transport (aioquic), Metrics, optionale SQLite-Persistenz.
- COULD: Desktop-Snippets, Mobile-Vorbereitung.
- WON’T (MVP): Internet-P2P, DHT/NAT-Traversal.

## Method (Kurz)
- Header (ver/flags/pad_len/t_epoch/win_ctr/salt/nonce), AEAD mit AAD=Header+Magic.
- Deterministische Hash-to-Vec Resonanz, θ=0.85.
- DAG (TTL), Replay-LRU, Poisson-Cover.
- Discovery via mDNS/DNS-SD; QUIC als Transport.

## Implementation (Staircase)
1. **M0 Scaffold**: Repo-Struktur, Apache-2.0 LICENSE, pyproject, API-Skelett.
2. **M1 Crypto+Packet**: HKDF, XChaCha, Fragment-Builder (1024B), Tests grün.
3. **M2 Resonanz+Replay**: tag_vec, cosine, ReplayCache, Tests grün.
4. **M3 Transport+Discovery**: aioquic Datagram, zeroconf Peers, 3-Node Compose tauscht Fragmente aus.
5. **M4 API+Metrics**: `/v1/inject`, `/v1/metrics`, e2e-Smoketest.
6. **M5 Docs**: README, Threat-Model, Quickstart.

## Milestones
M0..M5 wie oben, mit Abnahmekriterien (Tests, e2e).

## Gathering Results
- Konstantgrößenprüfung, Cover-Rate, Akzeptanzquote >90% bei θ>=0.85 in LAN-Test.
- CPU<50%, RAM<200MB in 3-Node-Compose bei 1k Fragmente/min.

## Need Professional Help in Developing Your Architecture?
https://sammuti.com
