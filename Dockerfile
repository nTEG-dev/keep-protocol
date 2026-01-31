FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY keep.proto .
COPY keep.go .

# Install protoc and the Go plugin
RUN apk add --no-cache protobuf protobuf-dev git
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest

# Generate protobuf code in current directory with package main
RUN protoc --go_out=paths=source_relative:. keep.proto

# Initialize module and build everything together
RUN go mod init keep && go mod tidy && go build -o keep .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/keep .
CMD ["./keep"]
