import socket
import keep_pb2  # <-- the generated file

p = keep_pb2.Packet()
p.typ = 0  # ask
p.id = "test-123"
p.src = "human:tester"
p.dst = "server"
p.body = "make tea please"

data = p.SerializeToString()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 9009))
s.sendall(data)
response = s.recv(4096)
s.close()

print("Sent:", p.body)
print("Received bytes:", response)
