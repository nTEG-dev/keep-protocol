# keep-protocol

**Lightweight signed TCP + Protobuf protocol for agent coordination.**

Agents send `Packet`s to a TCP endpoint (default `localhost:9009` or relay).
Unsigned or invalid sig → silent drop.
Valid ed25519 sig → parsed, logged, `"done"` reply.

## Key Features

- **ed25519 authentication** + integrity
- **Protobuf** for efficient, typed messages
- **fee + ttl** for anti-spam
- **Semantic dst routing** (e.g. `"swarm:sailing-planner"`)
- **Optional scar** for memory sharing

## Installation

```bash
docker run -d -p 9009:9009 ghcr.io/clcrawford-dev/keep-server:latest
```

## Usage in OpenClaw

Prompt your agent:

```text
Use keep-protocol to send intent to localhost:9009 body 'book sailing trip' src 'bot:me' dst 'server' fee 1000 ttl 300
```

Or use the Python SDK:

```python
from keep import KeepClient

client = KeepClient("localhost", 9009)
reply = client.send(body="ping", src="bot:me", dst="server")
print(reply.body)  # "done"
```

**Repo:** https://github.com/CLCrawford-dev/keep-protocol

---

🦞 claw-to-claw.
