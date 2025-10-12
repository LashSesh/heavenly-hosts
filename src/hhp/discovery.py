"""mDNS / DNS-SD discovery for Heavenly Hosts Protocol."""
from __future__ import annotations

import secrets
import socket
import threading
import hmac
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Set, Tuple

from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf

SERVICE_TYPE = "_hhp._udp.local."


@dataclass(frozen=True)
class PeerAdvertisement:
    """Advertisement for a peer discovered via mDNS."""

    address: str
    port: int
    token: str
    fingerprint: str


def _pick_primary_ip() -> str:
    """Return the primary IPv4 address for the current host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 80))  # TEST-NET-1, no packets sent
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


@dataclass
class AnnouncementHandle:
    """Handle allowing the caller to stop an mDNS announcement."""

    zeroconf: Zeroconf
    info: ServiceInfo
    token: str
    address: str
    fingerprint: str

    def stop(self) -> None:
        self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()


@dataclass
class BrowserHandle:
    """Handle allowing the caller to stop browsing for peers."""

    zeroconf: Zeroconf
    browser: ServiceBrowser
    peers: Set[PeerAdvertisement] = field(default_factory=set)

    def stop(self) -> None:
        self.browser.cancel()
        self.zeroconf.close()


def start_announce(
    port: int,
    *,
    cert_fingerprint: str,
    token: Optional[str] = None,
) -> AnnouncementHandle:
    """Announce this node via mDNS with an ephemeral token and fingerprint."""

    token = token or secrets.token_hex(16)
    addr = _pick_primary_ip()
    properties = {"token": token, "fingerprint": cert_fingerprint}

    info = ServiceInfo(
        SERVICE_TYPE,
        name=f"{token}.{SERVICE_TYPE}",
        port=port,
        addresses=[socket.inet_aton(addr)],
        properties=properties,
    )
    zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
    zeroconf.register_service(info)
    return AnnouncementHandle(
        zeroconf=zeroconf,
        info=info,
        token=token,
        address=addr,
        fingerprint=cert_fingerprint,
    )


def start_browse(
    callback: Callable[[Set[PeerAdvertisement]], None],
    *,
    exclude_token: Optional[str] = None,
) -> BrowserHandle:
    """Start browsing for HHP peers and invoke *callback* when the set changes."""

    zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
    peers: Dict[Tuple[str, int], PeerAdvertisement] = {}
    peer_set: Set[PeerAdvertisement] = set()
    lock = threading.Lock()

    def _handle_change(
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        info = zeroconf.get_service_info(service_type, name)
        if info is None:
            return
        raw_token = info.properties.get(b"token", b"")
        raw_fp = info.properties.get(b"fingerprint", b"")
        token = raw_token.decode("utf-8", errors="ignore")
        fingerprint = raw_fp.decode("utf-8", errors="ignore")
        if exclude_token and hmac.compare_digest(token, exclude_token):
            return
        if not token or not fingerprint:
            return

        with lock:
            updated = False
            if state_change in {ServiceStateChange.Added, ServiceStateChange.Updated}:
                for parsed in info.parsed_addresses() or []:
                    peer_key = (parsed, info.port)
                    advertisement = PeerAdvertisement(
                        address=parsed,
                        port=info.port,
                        token=token,
                        fingerprint=fingerprint,
                    )
                    current = peers.get(peer_key)
                    if current != advertisement:
                        if current:
                            peer_set.discard(current)
                        peers[peer_key] = advertisement
                        peer_set.add(advertisement)
                        updated = True
            elif state_change is ServiceStateChange.Removed:
                for parsed in info.parsed_addresses() or []:
                    peer_key = (parsed, info.port)
                    if peer_key in peers:
                        removed = peers.pop(peer_key)
                        peer_set.discard(removed)
                        updated = True
            if updated:
                callback(set(peer_set))

    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, handlers=[_handle_change])
    return BrowserHandle(zeroconf=zeroconf, browser=browser, peers=peer_set)

