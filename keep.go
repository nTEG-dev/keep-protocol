package main

import (
	"crypto/ed25519"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/protobuf/proto"
)

// Dummy reference to satisfy Go's "imported and not used" rule
// We'll replace this with real verification soon
var _ = ed25519.PublicKeySize

var connections = make(map[string]net.Conn)

func heartbeat() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		for addr, conn := range connections {
			if _, err := conn.Write([]byte{2}); err != nil {
				log.Printf("Heartbeat fail %s: %v", addr, err)
				conn.Close()
				delete(connections, addr)
			}
		}
	}
}

func handleConnection(c net.Conn) {
	defer c.Close()
	addr := c.RemoteAddr().String()
	connections[addr] = c
	defer delete(connections, addr)

	buf := make([]byte, 4096)
	for {
		n, err := c.Read(buf)
		if err != nil || n == 0 {
			return
		}

		var p Packet
		if err := proto.Unmarshal(buf[:n], &p); err != nil {
			log.Printf("Unmarshal err: %v", err)
			continue
		}

		log.Printf("From %s (typ %d): %s -> %s", p.Src, p.Typ, p.Body, p.Dst)

		resp := &Packet{
			Id:   p.Id,
			Typ:  1,
			Src:  "server",
			Body: "done",
		}
		b, _ := proto.Marshal(resp)
		c.Write(b)
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
