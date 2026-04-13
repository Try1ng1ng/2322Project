from __future__ import annotations

import socket


HOST = "127.0.0.1"
PORT = 8080


def receive_one_response(sock: socket.socket) -> bytes:
    buffer = b""

    # Read until the full header block arrives.
    while b"\r\n\r\n" not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            return buffer
        buffer += chunk

    header_block, body = buffer.split(b"\r\n\r\n", 1)
    headers_text = header_block.decode("iso-8859-1")
    content_length = 0

    for line in headers_text.split("\r\n")[1:]:
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break

    # Keep reading until the whole response body has arrived.
    while len(body) < content_length:
        chunk = sock.recv(4096)
        if not chunk:
            break
        body += chunk

    return header_block + b"\r\n\r\n" + body[:content_length]


def main() -> None:
    first_request = (
        "GET /hello.txt HTTP/1.1\r\n"
        "Host: 127.0.0.1:8080\r\n"
        "Connection: keep-alive\r\n"
        "\r\n"
    ).encode("iso-8859-1")

    second_request = (
        "GET /index.html HTTP/1.1\r\n"
        "Host: 127.0.0.1:8080\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("iso-8859-1")

    with socket.create_connection((HOST, PORT)) as sock:
        print("Sending first request on one socket...")
        sock.sendall(first_request)
        first_response = receive_one_response(sock)
        print(first_response.decode("iso-8859-1", errors="replace"))

        print("Sending second request on the same socket...")
        sock.sendall(second_request)
        second_response = receive_one_response(sock)
        print(second_response.decode("iso-8859-1", errors="replace"))


if __name__ == "__main__":
    main()
