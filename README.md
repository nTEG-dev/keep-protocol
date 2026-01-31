# keep-protocol

Lightweight TCP + Protobuf intent protocol for agent coordination.

Designed as simple, reliable plumbing so Moltbots / OpenClaw agents can send structured intents without central servers or heavy dependencies.

## Features
- Pure TCP server (no HTTP overhead)
- Protobuf messages for efficient, typed communication
- Simple `Packet` schema (src, dst, body, type, TTL, fee, etc.)
- Easy Docker deployment
- Built for concurrency and low resource use

## Run with Docker

### Build from source
```bash
# Clone the repo (if you haven't already)
git clone git@github.com:nTEG-dev/keep-protocol.git
cd keep-protocol

# Build
docker build -t keep-protocol .

# Run the server
docker run -d -p 9009:9009 --name keep-server keep-protocol
Or pull pre-built (when published)
Bashdocker pull ghcr.io/nTEG-dev/keep-protocol:latest
docker run -d -p 9009:9009 --name keep-server ghcr.io/nTEG-dev/keep-protocol:latest
Agents connect to localhost:9009 (or the host IP:9009) and send serialized Packet messages.
