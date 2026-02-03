"""Keep protocol client -- sign and send packets over TCP."""

import socket
import struct
import uuid
from typing import Callable, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from keep import keep_pb2

MAX_PACKET_SIZE = 65536


class KeepClient:
    """Client for the keep-protocol server.

    Generates an ephemeral ed25519 keypair on init (or accepts an existing one).
    Signs every outgoing packet.

    Supports two modes:
      - Ephemeral (default): opens/closes a TCP connection per send() call.
      - Persistent: call connect() or use as context manager to hold a connection
        open for sending and receiving routed messages via listen().
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9009,
        private_key: Optional[Ed25519PrivateKey] = None,
        timeout: float = 10.0,
        src: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.src = src or "bot:keep-client"
        self._private_key = private_key or Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self._pk_bytes = self._public_key.public_bytes_raw()
        self._sock: Optional[socket.socket] = None

    # -- Connection management --

    def connect(self) -> None:
        """Open a persistent TCP connection to the server."""
        if self._sock is not None:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect((self.host, self.port))
        self._sock = s

    def disconnect(self) -> None:
        """Close the persistent connection."""
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def __enter__(self) -> "KeepClient":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.disconnect()

    # -- Framing helpers --

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

    @classmethod
    def _read_packet(cls, sock: socket.socket) -> keep_pb2.Packet:
        """Read and parse one framed Packet from sock."""
        data = cls._recv_framed(sock)
        p = keep_pb2.Packet()
        p.ParseFromString(data)
        return p

    # -- Signing --

    def _sign_packet(
        self,
        body: str,
        src: Optional[str] = None,
        dst: str = "server",
        typ: int = 0,
        fee: int = 0,
        ttl: int = 60,
        msg_id: Optional[str] = None,
        scar: bytes = b"",
    ) -> bytes:
        """Build, sign, and serialize a Packet. Returns wire bytes."""
        msg_id = msg_id or str(uuid.uuid4())
        src = src or self.src

        p = keep_pb2.Packet()
        p.typ = typ
        p.id = msg_id
        p.src = src
        p.dst = dst
        p.body = body
        p.fee = fee
        p.ttl = ttl
        p.scar = scar

        sign_payload = p.SerializeToString()
        sig_bytes = self._private_key.sign(sign_payload)

        p.sig = sig_bytes
        p.pk = self._pk_bytes
        return p.SerializeToString()

    # -- Send --

    def send(
        self,
        body: str,
        src: Optional[str] = None,
        dst: str = "server",
        typ: int = 0,
        fee: int = 0,
        ttl: int = 60,
        msg_id: Optional[str] = None,
        scar: bytes = b"",
        wait_reply: Optional[bool] = None,
    ) -> Optional[keep_pb2.Packet]:
        """Sign and send a packet.

        In ephemeral mode (no connect() called): opens a connection, sends,
        reads the reply, and closes. Always returns the server's reply.

        In persistent mode: sends on the open connection.
          - wait_reply=True: blocks until a reply is received and returns it.
          - wait_reply=False: sends without waiting. Returns None.
          - wait_reply=None (default): waits if dst is "server" or "",
            does not wait otherwise.
        """
        wire_data = self._sign_packet(
            body=body,
            src=src,
            dst=dst,
            typ=typ,
            fee=fee,
            ttl=ttl,
            msg_id=msg_id,
            scar=scar,
        )

        if self._sock is not None:
            # Persistent mode
            self._send_framed(self._sock, wire_data)

            should_wait = wait_reply
            if should_wait is None:
                should_wait = dst in ("server", "")

            if should_wait:
                return self._read_packet(self._sock)
            return None

        # Ephemeral mode — open/close per call
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

    # -- Listen --

    def listen(
        self,
        callback: Callable[[keep_pb2.Packet], None],
        timeout: Optional[float] = None,
    ) -> None:
        """Block and read packets from the persistent connection.

        Invokes callback(packet) for each received packet.
        Heartbeat packets (typ=2) are silently filtered.

        Args:
            callback: Called with each received Packet.
            timeout: Seconds to listen before returning. None = listen until
                     the connection closes or an error occurs.

        Raises:
            RuntimeError: If not connected (call connect() first).
        """
        if self._sock is None:
            raise RuntimeError("Not connected. Call connect() first.")

        if timeout is not None:
            self._sock.settimeout(timeout)

        try:
            while True:
                p = self._read_packet(self._sock)
                # Filter heartbeat packets
                if p.typ == 2:
                    continue
                callback(p)
        except socket.timeout:
            return
        except ConnectionError:
            return
        finally:
            if timeout is not None:
                self._sock.settimeout(self.timeout)
