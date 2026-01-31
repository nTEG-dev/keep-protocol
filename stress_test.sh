#!/bin/bash

for i in {1..20}; do
  (
    python3 -c "
import keep_pb2
import socket
import time

p = keep_pb2.Packet()
p.typ = 0
p.id = 'stress-$i'
p.src = 'human:loadtest'
p.dst = 'server'
p.body = 'Quick stress test $i'

data = p.SerializeToString()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 9009))
s.sendall(data)
s.close()
" &
  )
done
wait

echo "All 20 sent. Checking logs..."
docker logs keep-server --tail 30
