"""QUIC Datagram transport wiring for HHP."""
from __future__ import annotations

import asyncio
import contextlib
import secrets
import ssl
import struct
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.asyncio.client import connect
from aioquic.asyncio.server import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import ConnectionTerminated, DatagramFrameReceived, HandshakeCompleted
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from . import cover, discovery
from .config import Cfg, DEFAULT_FRAGMENT_SIZE
from .crypto import aead_decrypt, derive_topic_key
from .dag import DAG
from .packet import AAD_MAGIC, HDR_FMT, build_fragment, unpack_header
from .replay import ReplayCache
from .resonance import tag_vec

Peer = Tuple[str, int]


def _generate_ephemeral_cert(common_name: str) -> Tuple[bytes, bytes]:
    key = ec.generate_private_key(ec.SECP256R1())
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(common_name)]), critical=False)
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


class HHPQuicProtocol(QuicConnectionProtocol):
    """Shared QUIC protocol implementation for both client and server roles."""

    def __init__(self, transport: "HHPTransport", peer: Optional[Peer], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._transport = transport
        self.peer = peer

    def quic_event_received(self, event) -> None:  # type: ignore[override]
        if isinstance(event, HandshakeCompleted):
            if self.peer is None:
                path = self._quic._network_paths[0]  # type: ignore[attr-defined]
                self.peer = (path.addr[0], path.addr[1])
            self._transport.on_protocol_ready(self)
        elif isinstance(event, DatagramFrameReceived):
            asyncio.create_task(self._transport.process_fragment(event.data))
        elif isinstance(event, ConnectionTerminated):
            self._transport.on_protocol_closed(self)
        else:
            super().quic_event_received(event)


class HHPTransport:
    """Manages QUIC transport, discovery, cover traffic, and metrics."""

    def __init__(
        self,
        cfg: Cfg,
        dag: DAG,
        replay: ReplayCache,
        metrics: Dict[str, int],
        known_tags: Set[str],
    ) -> None:
        self._cfg = cfg
        self._dag = dag
        self._replay = replay
        self._metrics = metrics
        self._known_tags = known_tags
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._announce_handle: Optional[discovery.AnnouncementHandle] = None
        self._browser_handle: Optional[discovery.BrowserHandle] = None
        self._server = None
        self._client_tasks: Dict[Peer, asyncio.Task[None]] = {}
        self._client_protocols: Dict[Peer, HHPQuicProtocol] = {}
        self._cover_task: Optional[asyncio.Task[None]] = None
        self._tx_counter = 0
        self._fragment_size = DEFAULT_FRAGMENT_SIZE

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._announce_handle = discovery.start_announce(self._cfg.transport.port)
        self._browser_handle = discovery.start_browse(
            lambda peers: asyncio.run_coroutine_threadsafe(
                self._update_peers(peers), self._loop
            ),
            exclude_token=self._announce_handle.token,
        )
        self._server = await serve(
            host="0.0.0.0",
            port=self._cfg.transport.port,
            configuration=self._server_config(),
            create_protocol=lambda *a, **kw: HHPQuicProtocol(self, None, *a, **kw),
        )
        if self._cfg.cover.enabled:
            self._cover_task = asyncio.create_task(
                cover.run_cover(self._send_cover_fragment, self._cfg.cover.mean_rate_per_min)
            )

    async def stop(self) -> None:
        if self._cover_task:
            self._cover_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cover_task
        if self._browser_handle:
            self._browser_handle.stop()
            self._browser_handle = None
        if self._announce_handle:
            self._announce_handle.stop()
            self._announce_handle = None
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        for task in list(self._client_tasks.values()):
            task.cancel()
        for task in list(self._client_tasks.values()):
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._client_tasks.clear()
        self._client_protocols.clear()

    def on_protocol_ready(self, protocol: HHPQuicProtocol) -> None:
        if protocol.peer is None:
            return
        self._client_protocols[protocol.peer] = protocol

    def on_protocol_closed(self, protocol: HHPQuicProtocol) -> None:
        peer = protocol.peer
        if peer and peer in self._client_protocols:
            self._client_protocols.pop(peer, None)

    async def _update_peers(self, peers: Set[Peer]) -> None:
        existing = set(self._client_tasks.keys())
        for peer in peers:
            if (
                self._announce_handle
                and peer[0] == self._announce_handle.address
                and peer[1] == self._cfg.transport.port
            ):
                continue
            if peer not in existing:
                self._client_tasks[peer] = asyncio.create_task(self._connect_peer(peer))
        for peer in existing - peers:
            task = self._client_tasks.pop(peer, None)
            if task:
                task.cancel()
            self._client_protocols.pop(peer, None)

    async def _connect_peer(self, peer: Peer) -> None:
        configuration = self._client_config()
        try:
            async with connect(
                peer[0],
                peer[1],
                configuration=configuration,
                create_protocol=lambda *a, **kw: HHPQuicProtocol(self, peer, *a, **kw),
            ) as client:
                await client.wait_connected()
                self._client_protocols[peer] = client  # type: ignore[assignment]
                await client.wait_closed()
        except Exception:
            await asyncio.sleep(1.0)
        finally:
            self._client_protocols.pop(peer, None)
            self._client_tasks.pop(peer, None)

    async def transmit(self, tag: str, payload: bytes, *, cover: bool = False) -> None:
        if not payload and not cover:
            return
        fragment = self._build_fragment(tag, payload, cover=cover)
        await self._broadcast(fragment)
        self._metrics["fragments_tx"] = self._metrics.get("fragments_tx", 0) + 1

    async def _send_cover_fragment(self, cover: bool = False) -> None:
        tag = secrets.token_hex(8)
        payload = secrets.token_bytes(32)
        await self.transmit(tag, payload, cover=True)

    async def _broadcast(self, fragment: bytes) -> None:
        for peer, protocol in list(self._client_protocols.items()):
            try:
                protocol._quic.send_datagram_frame(fragment)
                protocol.transmit()
            except Exception:
                self._client_protocols.pop(peer, None)

    def _build_fragment(self, tag: str, payload: bytes, *, cover: bool) -> bytes:
        t_epoch = int(time.time())
        self._tx_counter = (self._tx_counter + 1) % (1 << 31)
        return build_fragment(
            tag=tag,
            payload=payload,
            t_epoch=t_epoch,
            win_ctr=self._tx_counter,
            fragment_size=self._fragment_size,
            cover=cover,
        )

    async def process_fragment(self, fragment: bytes) -> None:
        if len(fragment) != self._fragment_size:
            return
        header = unpack_header(fragment)
        if self._replay.seen(header.t_epoch, header.win_ctr, header.nonce):
            return
        aad = fragment[: struct.calcsize(HDR_FMT)] + AAD_MAGIC
        ciphertext = fragment[len(aad) :]
        matched_tag: Optional[str] = None
        payload: Optional[bytes] = None
        for tag in list(self._known_tags):
            try:
                key = derive_topic_key(tag, header.salt)
                plaintext = aead_decrypt(key, header.nonce, aad, ciphertext)
                if header.pad_len:
                    plaintext = plaintext[: -header.pad_len]
                matched_tag = tag
                payload = plaintext
                break
            except Exception:
                continue
        if matched_tag is None or payload is None:
            return
        vec = tag_vec(matched_tag)
        self._dag.insert_cell(vec.tobytes())
        self._metrics["fragments_rx"] = self._metrics.get("fragments_rx", 0) + 1

    def _server_config(self) -> QuicConfiguration:
        configuration = QuicConfiguration(is_client=False, alpn_protocols=["hhp/1"])
        configuration.max_datagram_frame_size = self._fragment_size
        cert_pem, key_pem = _generate_ephemeral_cert(secrets.token_hex(6))
        with tempfile.NamedTemporaryFile(delete=False) as cert_file:
            cert_path = Path(cert_file.name)
            cert_file.write(cert_pem + key_pem)
        try:
            configuration.load_cert_chain(str(cert_path))
        finally:
            cert_path.unlink(missing_ok=True)
        return configuration

    def _client_config(self) -> QuicConfiguration:
        configuration = QuicConfiguration(is_client=True, alpn_protocols=["hhp/1"])
        configuration.max_datagram_frame_size = self._fragment_size
        configuration.verify_mode = ssl.CERT_NONE
        return configuration

