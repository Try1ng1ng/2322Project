from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote


SERVER_NAME = "COMP2322PythonServer/0.1"
SUPPORTED_METHODS = {"GET", "HEAD"}
SUPPORTED_VERSIONS = {"HTTP/1.0", "HTTP/1.1"}
MAX_HEADER_BYTES = 65536
# All requested files must stay inside this directory.
WEB_ROOT = Path(__file__).resolve().parent / "www"


class HttpParseError(Exception):
    pass


@dataclass
class HttpRequest:
    method: str
    path: str
    version: str
    headers: dict[str, str]


def format_http_date() -> str:
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def receive_http_request(client_socket) -> bytes:
    chunks = []
    total_size = 0

    while True:
        # Read the request in small chunks until the header section is complete.
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
    if not request_data:
        raise HttpParseError("empty request")

    try:
        request_text = request_data.decode("iso-8859-1")
    except UnicodeDecodeError as exc:
        raise HttpParseError("request contains invalid bytes") from exc

    if "\r\n\r\n" not in request_text:
        raise HttpParseError("request headers are incomplete")

    # Only the header block is needed at this project stage.
    header_section = request_text.split("\r\n\r\n", 1)[0]
    lines = header_section.split("\r\n")
    if not lines or not lines[0].strip():
        raise HttpParseError("missing request line")

    # The request line should look like: GET /index.html HTTP/1.1
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
    headers: dict[str, str] = {}

    for line in header_lines:
        if not line:
            continue
        if ":" not in line:
            raise HttpParseError(f"malformed header line: {line}")

        # Split only once so header values may still contain ':' characters.
        name, value = line.split(":", 1)
        name = name.strip().lower()
        value = value.strip()

        if not name:
            raise HttpParseError("header name cannot be empty")

        headers[name] = value

    return headers


def resolve_request_path(request_path: str) -> Path:
    # Ignore query strings for static file lookup.
    clean_path = request_path.split("?", 1)[0].split("#", 1)[0]
    decoded_path = unquote(clean_path)

    # Map the site root to the default page.
    if decoded_path == "/":
        decoded_path = "/index.html"

    relative_path = decoded_path.lstrip("/")
    target_path = (WEB_ROOT / relative_path).resolve()

    # Block attempts to escape the web root, such as ../secret.txt
    if WEB_ROOT.resolve() not in target_path.parents and target_path != WEB_ROOT.resolve():
        raise PermissionError("requested path is outside the web root")

    return target_path


def get_content_type(file_path: Path) -> str:
    # Fall back to a binary type when Python cannot guess the extension.
    content_type, _ = mimetypes.guess_type(file_path.name)
    return content_type or "application/octet-stream"


def read_requested_file(file_path: Path) -> bytes:
    return file_path.read_bytes()


def build_http_response(
    status_code: int,
    reason_phrase: str,
    body: bytes = b"",
    method: str = "GET",
    extra_headers: dict[str, str] | None = None,
) -> bytes:
    # Build the minimum headers needed for this project stage.
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

    # HEAD responses must not include a body.
    if method == "HEAD":
        return response_head
    return response_head + body
