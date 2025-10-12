"""mDNS / DNS-SD discovery for Heavenly Hosts Protocol."""
from __future__ import annotations

import secrets
import socket
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional, Set, Tuple

from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf

SERVICE_TYPE = "_hhp._udp.local."


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

    def stop(self) -> None:
        self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()


@dataclass
class BrowserHandle:
    """Handle allowing the caller to stop browsing for peers."""

    zeroconf: Zeroconf
    browser: ServiceBrowser
    peers: Set[Tuple[str, int]] = field(default_factory=set)

    def stop(self) -> None:
        self.browser.cancel()
        self.zeroconf.close()


def start_announce(port: int) -> AnnouncementHandle:
    """Announce this node via mDNS with an ephemeral token."""

    token = secrets.token_hex(8)
    addr = _pick_primary_ip()
    properties = {"token": token}

    info = ServiceInfo(
        SERVICE_TYPE,
        name=f"{token}.{SERVICE_TYPE}",
        port=port,
        addresses=[socket.inet_aton(addr)],
        properties=properties,
    )
    zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
    zeroconf.register_service(info)
    return AnnouncementHandle(zeroconf=zeroconf, info=info, token=token, address=addr)


def start_browse(
    callback: Callable[[Set[Tuple[str, int]]], None],
    *,
    exclude_token: Optional[str] = None,
) -> BrowserHandle:
    """Start browsing for HHP peers and invoke *callback* when the set changes."""

    zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
    peers: Set[Tuple[str, int]] = set()
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
        token = info.properties.get(b"token", b"").decode("utf-8", errors="ignore")
        if exclude_token and token == exclude_token:
            return

        with lock:
            updated = False
            if state_change in {ServiceStateChange.Added, ServiceStateChange.Updated}:
                for parsed in info.parsed_addresses() or []:
                    peer = (parsed, info.port)
                    if peer not in peers:
                        peers.add(peer)
                        updated = True
            elif state_change is ServiceStateChange.Removed:
                for parsed in info.parsed_addresses() or []:
                    peer = (parsed, info.port)
                    if peer in peers:
                        peers.remove(peer)
                        updated = True
            if updated:
                callback(set(peers))

    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, handlers=[_handle_change])
    return BrowserHandle(zeroconf=zeroconf, browser=browser, peers=peers)

