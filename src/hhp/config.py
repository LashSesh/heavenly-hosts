from dataclasses import dataclass
from pathlib import Path
import yaml

DEFAULT_FRAGMENT_SIZE = 1024
DEFAULT_THRESHOLD = 0.85

@dataclass
class TransportCfg:
    mode: str = "quic"
    port: int = 4444
    fragment_size: int = DEFAULT_FRAGMENT_SIZE
    mtu: int = 1280

@dataclass
class CryptoCfg:
    aead: str = "xchacha20poly1305"
    hkdf_hash: str = "sha256"
    topic_threshold: float = DEFAULT_THRESHOLD
    replay_window_ttl: int = 600
    max_replay_entries: int = 100_000

@dataclass
class DiscoveryCfg:
    service: str = "_hhp._udp.local"
    interval_ms: int = 5000

@dataclass
class CoverCfg:
    enabled: bool = True
    mean_rate_per_min: int = 20

@dataclass
class Cfg:
    transport: TransportCfg = TransportCfg()
    crypto: CryptoCfg = CryptoCfg()
    discovery: DiscoveryCfg = DiscoveryCfg()
    cover: CoverCfg = CoverCfg()

def load(path: Path) -> Cfg:
    doc = yaml.safe_load(path.read_text())
    # Minimal mapping for MVP
    cfg = Cfg()
    t = doc.get('transport', {})
    c = doc.get('crypto', {})
    d = doc.get('discovery', {})
    v = doc.get('cover', {})
    cfg.transport.port = int(t.get('port', cfg.transport.port))
    cfg.transport.fragment_size = int(t.get('fragment_size', cfg.transport.fragment_size))
    cfg.crypto.topic_threshold = float(c.get('topic_threshold', cfg.crypto.topic_threshold))
    cfg.discovery.service = d.get('service', cfg.discovery.service)
    cfg.cover.enabled = bool(v.get('enabled', cfg.cover.enabled))
    cfg.cover.mean_rate_per_min = int(v.get('mean_rate_per_min', cfg.cover.mean_rate_per_min))
    return cfg
