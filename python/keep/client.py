"""Keep protocol client -- sign and send packets over TCP."""

import socket
import struct
import uuid
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from keep import keep_pb2

MAX_PACKET_SIZE = 65536


class KeepClient:
    """Client for the keep-protocol server.

    Generates an ephemeral ed25519 keypair on init (or accepts an existing one).
    Signs every outgoing packet.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9009,
        private_key: Optional[Ed25519PrivateKey] = None,
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._private_key = private_key or Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self._pk_bytes = self._public_key.public_bytes_raw()

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> bytes:
        """Read exactly n bytes from sock."""
        chunks = []
        remaining = n
        while remaining > 0:
            chunk = sock.recv(min(remaining, 4096))
            if not chunk:
                raise ConnectionError(
                    f"Connection closed: expected {n} bytes, got {n - remaining}"
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    @staticmethod
    def _send_framed(sock: socket.socket, data: bytes) -> None:
        """Send data with a 4-byte big-endian length prefix."""
        if len(data) > MAX_PACKET_SIZE:
            raise ValueError(f"Packet too large: {len(data)} > {MAX_PACKET_SIZE}")
        header = struct.pack(">I", len(data))
        sock.sendall(header + data)

    @classmethod
    def _recv_framed(cls, sock: socket.socket) -> bytes:
        """Read a length-prefixed frame: 4-byte BE header + payload."""
        header = cls._recv_exact(sock, 4)
        (msg_len,) = struct.unpack(">I", header)
        if msg_len == 0:
            raise ConnectionError("Received zero-length frame")
        if msg_len > MAX_PACKET_SIZE:
            raise ConnectionError(f"Frame too large: {msg_len} > {MAX_PACKET_SIZE}")
        return cls._recv_exact(sock, msg_len)

    def send(
        self,
        body: str,
        src: str = "bot:keep-client",
        dst: str = "server",
        typ: int = 0,
        fee: int = 0,
        ttl: int = 60,
        msg_id: Optional[str] = None,
        scar: bytes = b"",
    ) -> keep_pb2.Packet:
        """Sign and send a packet, return the server's reply."""
        msg_id = msg_id or str(uuid.uuid4())

        # Build unsigned packet
        p = keep_pb2.Packet()
        p.typ = typ
        p.id = msg_id
        p.src = src
        p.dst = dst
        p.body = body
        p.fee = fee
        p.ttl = ttl
        p.scar = scar

        # Sign
        sign_payload = p.SerializeToString()
        sig_bytes = self._private_key.sign(sign_payload)

        # Set sig + pk
        p.sig = sig_bytes
        p.pk = self._pk_bytes
        wire_data = p.SerializeToString()

        # Send over TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect((self.host, self.port))
            self._send_framed(s, wire_data)
            reply_data = self._recv_framed(s)
        finally:
            s.close()

        resp = keep_pb2.Packet()
        resp.ParseFromString(reply_data)
        return resp
