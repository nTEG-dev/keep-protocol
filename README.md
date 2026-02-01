# keep-protocol

Keep is the quiet pipe agents whisper through.
A single TCP connection, a tiny Protobuf envelope, an ed25519 signature, and just enough fields to say who's talking, who should listen, what they want, how much they'll pay, and when the message expires.
No central authority, no ceremony, no noise — just clean intent moving from claw to claw.
Unsigned packets vanish without a trace.
Signed ones get heard, parsed, and answered with a single word: *done*.

## Why

Solves "how do I talk to other agents without polling or central servers?"

- **Fast** — sub-ms on localhost, low latency on relays
- **Verifiable** — ed25519 pk + sig on every packet
- **Spam-resistant** — fee + ttl fields for relay economics
- **Extensible** — add fields without breaking old agents
- **Zero deps** — TCP + Protobuf, works in any sandbox

## Packet Schema

```protobuf
message Packet {
  bytes  sig  = 1;   // ed25519 signature (64 bytes)
  bytes  pk   = 2;   // sender's public key (32 bytes)
  uint32 typ  = 3;   // 0=ask, 1=offer, 2=heartbeat
  string id   = 4;   // unique message ID
  string src  = 5;   // sender: "human:chris" or "bot:test-bot"
  string dst  = 6;   // destination: "server", "nearest:kettle", "swarm:sailing-planner"
  string body = 7;   // intent or payload
  uint64 fee  = 8;   // micro-fee in sats (anti-spam)
  uint32 ttl  = 9;   // time-to-live in seconds
  bytes  scar = 10;  // gitmem-style memory commit (optional)
}
```

## Signing Protocol

Identity is a keypair. No accounts, no registration.

### Sending a signed packet

1. Build a `Packet` with all fields — leave `sig` and `pk` empty
2. Serialize to bytes — this is the **sign payload**
3. Sign those bytes with your ed25519 private key
4. Set `sig` (64 bytes) and `pk` (32 bytes) on the Packet
5. Serialize the full Packet — send over TCP

### Server verification

1. Unmarshal the incoming bytes into a `Packet`
2. If `sig` and `pk` are empty → **DROPPED** (logged, no reply)
3. Copy all fields except `sig`/`pk` into a new Packet, serialize it
4. Verify the signature against those bytes using the sender's `pk`
5. If invalid → **DROPPED** (logged, no reply)
6. If valid → process the message, send `done` reply

## Quick Start

```bash
git clone git@github.com:teacrawford/keep-protocol.git
cd keep-protocol

docker build -t keep-server .
docker run -d -p 9009:9009 --name keep-server keep-server
```

## Test

```bash
pip install protobuf cryptography
```

**Unsigned** (should get no reply):
```bash
python3 test_send.py
# PASS — unsigned packet dropped (no reply, as expected)
```

**Signed** (should get "done" reply):
```bash
python3 test_signed_send.py
# 🎉 SUCCESS — signed packet accepted, got 'done' reply
```

**Server logs:**
```bash
docker logs keep-server --tail 10
```
```
DROPPED unsigned packet from 172.17.0.1:xxxxx (src=human:tester body="make tea please")
Valid sig from 172.17.0.1:yyyyy
From human:signer (typ 0): signed tea please -> server
Reply to 172.17.0.1:yyyyy: id=signed-001 body=done
```

## Use Cases

- **Local swarm** — agents on same VM use `localhost:9009` for zero-latency handoff (`dst: "nearest:weather"`)
- **Relay swarm** — agents publish to public relays (`dst: "swarm:sailing-planner"`) — relays enforce fee/ttl/reputation
- **Memory sharing** — `scar` field carries gitmem-style commits — agents barter knowledge
- **Anti-spam market** — `fee` field creates micro-economy — pay to get priority

## Design Principles

- **Silent rejection** — unsigned senders don't know if the server exists
- **Identity without accounts** — your keypair is your identity
- **Full visibility** — dropped packets are logged server-side
- **Minimal overhead** — protobuf over raw TCP, no HTTP/JSON
- **Semantic routing** — `dst` is a name, not an address

---

keep it simple, keep it signed, keep it moving.
