"""Keep protocol client -- sign and send packets over TCP."""

import socket
import uuid
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from keep import keep_pb2


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
            s.sendall(wire_data)
            reply_data = s.recv(4096)
        finally:
            s.close()

        resp = keep_pb2.Packet()
        resp.ParseFromString(reply_data)
        return resp
