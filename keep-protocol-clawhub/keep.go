package main

import (
	"crypto/ed25519"
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"google.golang.org/protobuf/proto"
)

const MaxPacketSize = 65536

var (
	connections = make(map[string]net.Conn)
	connMu      sync.Mutex
)

// readPacket reads a length-prefixed protobuf Packet from conn.
// Wire format: [4 bytes big-endian uint32 length][length bytes protobuf].
func readPacket(conn net.Conn) (*Packet, error) {
	var lenBuf [4]byte
	if _, err := io.ReadFull(conn, lenBuf[:]); err != nil {
		return nil, err
	}
	msgLen := binary.BigEndian.Uint32(lenBuf[:])

	if msgLen == 0 {
		return nil, fmt.Errorf("zero-length packet")
	}
	if msgLen > MaxPacketSize {
		return nil, fmt.Errorf("packet too large: %d > %d", msgLen, MaxPacketSize)
	}

	payload := make([]byte, msgLen)
	if _, err := io.ReadFull(conn, payload); err != nil {
		return nil, err
	}

	var p Packet
	if err := proto.Unmarshal(payload, &p); err != nil {
		return nil, fmt.Errorf("unmarshal: %w", err)
	}
	return &p, nil
}

// writePacket serializes a Packet with a 4-byte big-endian length prefix and writes it to conn.
func writePacket(conn net.Conn, p *Packet) error {
	data, err := proto.Marshal(p)
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	if len(data) > MaxPacketSize {
		return fmt.Errorf("packet too large: %d > %d", len(data), MaxPacketSize)
	}

	var lenBuf [4]byte
	binary.BigEndian.PutUint32(lenBuf[:], uint32(len(data)))

	if _, err := conn.Write(lenBuf[:]); err != nil {
		return err
	}
	if _, err := conn.Write(data); err != nil {
		return err
	}
	return nil
}

func heartbeat() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		hb := &Packet{
			Typ: 2,
			Src: "server",
		}
		connMu.Lock()
		for addr, conn := range connections {
			if err := writePacket(conn, hb); err != nil {
				log.Printf("Heartbeat fail %s: %v", addr, err)
				conn.Close()
				delete(connections, addr)
			}
		}
		connMu.Unlock()
	}
}

// verifySig checks the ed25519 signature on a Packet.
// The signed payload is the Packet with sig and pk zeroed out, then serialized.
func verifySig(p *Packet) bool {
	if len(p.Sig) == 0 || len(p.Pk) == 0 {
		return false // unsigned packet
	}
	if len(p.Pk) != ed25519.PublicKeySize {
		log.Printf("Malformed pk: expected %d bytes, got %d", ed25519.PublicKeySize, len(p.Pk))
		return false
	}
	if len(p.Sig) != ed25519.SignatureSize {
		log.Printf("Malformed sig: expected %d bytes, got %d", ed25519.SignatureSize, len(p.Sig))
		return false
	}

	// Reconstruct the exact bytes that were signed:
	// a copy of the packet with sig and pk cleared.
	signCopy := &Packet{
		Typ:  p.Typ,
		Id:   p.Id,
		Src:  p.Src,
		Dst:  p.Dst,
		Body: p.Body,
		Fee:  p.Fee,
		Ttl:  p.Ttl,
		Scar: p.Scar,
		// Sig and Pk intentionally omitted (zero value)
	}
	signBytes, err := proto.Marshal(signCopy)
	if err != nil {
		log.Printf("Marshal for verify failed: %v", err)
		return false
	}

	return ed25519.Verify(p.Pk, signBytes, p.Sig)
}

func handleConnection(c net.Conn) {
	defer c.Close()
	addr := c.RemoteAddr().String()
	connMu.Lock()
	connections[addr] = c
	connMu.Unlock()
	defer func() {
		connMu.Lock()
		delete(connections, addr)
		connMu.Unlock()
	}()

	for {
		p, err := readPacket(c)
		if err != nil {
			if err != io.EOF {
				log.Printf("Read error from %s: %v", addr, err)
			}
			return
		}

		// Signature is REQUIRED — unsigned packets are logged and dropped
		if len(p.Sig) == 0 && len(p.Pk) == 0 {
			log.Printf("DROPPED unsigned packet from %s (src=%s body=%q)", addr, p.Src, p.Body)
			continue
		}

		if !verifySig(p) {
			log.Printf("DROPPED invalid sig from %s (src=%s)", addr, p.Src)
			continue
		}

		log.Printf("Valid sig from %s", addr)
		log.Printf("From %s (typ %d): %s -> %s", p.Src, p.Typ, p.Body, p.Dst)

		resp := &Packet{
			Id:   p.Id,
			Typ:  1,
			Src:  "server",
			Body: "done",
		}
		if err := writePacket(c, resp); err != nil {
			log.Printf("Write error to %s: %v", addr, err)
			return
		}
		log.Printf("Reply to %s: id=%s body=%s", addr, resp.Id, resp.Body)
	}
}

func main() {
	l, err := net.Listen("tcp", ":9009")
	if err != nil {
		log.Fatal(err)
	}
	log.Println("keep listening on :9009")

	go heartbeat()

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sig
		log.Println("Shutdown")
		os.Exit(0)
	}()

	for {
		conn, err := l.Accept()
		if err != nil {
			continue
		}
		go handleConnection(conn)
	}
}
