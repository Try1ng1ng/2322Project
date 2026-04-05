"""Utility helpers for HTTP parsing and basic response construction.

This module keeps the protocol-specific logic out of ``server.py`` so the
main program can stay focused on socket setup and connection handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


SERVER_NAME = "COMP2322PythonServer/0.1"
SUPPORTED_METHODS = {"GET", "HEAD"}
SUPPORTED_VERSIONS = {"HTTP/1.0", "HTTP/1.1"}
MAX_HEADER_BYTES = 65536


class HttpParseError(Exception):
    #Raised when the incoming HTTP request is invalid.


@dataclass
class HttpRequest:
    #Simple representation of a parsed HTTP request."

    method: str
    path: str
    version: str
    headers: dict[str, str]


def format_http_date() -> str:
    #Return the current time in the standard HTTP-date format.
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def receive_http_request(client_socket) -> bytes:
    #Read from the socket until the HTTP header terminator is received.


    chunks = []
    total_size = 0

    while True:
        chunk = client_socket.recv(4096)
        if not chunk:
            break

        chunks.append(chunk)
        total_size += len(chunk)
        request_data = b"".join(chunks)

        if b"\r\n\r\n" in request_data:
            return request_data

        if total_size > MAX_HEADER_BYTES:
            raise HttpParseError("request headers are too large")

    return b"".join(chunks)


def parse_http_request(request_data: bytes) -> HttpRequest:

    #Parse a raw HTTP request into method, path, version, and headers.
    if not request_data:
        raise HttpParseError("empty request")

    try:
        request_text = request_data.decode("iso-8859-1")
    except UnicodeDecodeError as exc:
        raise HttpParseError("request contains invalid bytes") from exc

    if "\r\n\r\n" not in request_text:
        raise HttpParseError("request headers are incomplete")

    header_section = request_text.split("\r\n\r\n", 1)[0]
    lines = header_section.split("\r\n")
    if not lines or not lines[0].strip():
        raise HttpParseError("missing request line")

    request_line_parts = lines[0].split()
    if len(request_line_parts) != 3:
        raise HttpParseError("request line must contain method, path, and version")

    method, path, version = request_line_parts
    method = method.upper()

    if method not in SUPPORTED_METHODS:
        raise HttpParseError("unsupported HTTP method")

    if version not in SUPPORTED_VERSIONS:
        raise HttpParseError("unsupported HTTP version")

    if not path.startswith("/"):
        raise HttpParseError("request path must start with '/'")

    headers = parse_headers(lines[1:])
    return HttpRequest(method=method, path=path, version=version, headers=headers)


def parse_headers(header_lines: list[str]) -> dict[str, str]:
    #Parse HTTP headers and normalize names to lowercase.
    headers: dict[str, str] = {}

    for line in header_lines:
        if not line:
            continue
        if ":" not in line:
            raise HttpParseError(f"malformed header line: {line}")

        name, value = line.split(":", 1)
        name = name.strip().lower()
        value = value.strip()

        if not name:
            raise HttpParseError("header name cannot be empty")

        headers[name] = value

    return headers


def build_http_response(
    status_code: int,
    reason_phrase: str,
    body: bytes = b"",
    method: str = "GET",
    extra_headers: dict[str, str] | None = None,
) -> bytes:
    
    #Build a minimal HTTP response message for the current project stage.
    headers = {
        "Date": format_http_date(),
        "Server": SERVER_NAME,
        "Connection": "close",
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Length": str(len(body)),
    }

    if extra_headers:
        headers.update(extra_headers)

    response_lines = [f"HTTP/1.1 {status_code} {reason_phrase}"]
    response_lines.extend(f"{key}: {value}" for key, value in headers.items())
    response_head = "\r\n".join(response_lines).encode("iso-8859-1") + b"\r\n\r\n"

    if method == "HEAD":
        return response_head
    return response_head + body
