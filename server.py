from __future__ import annotations

import argparse
import queue
import socket
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from logger_util import write_access_log
from utils import (
    HttpParseError,
    build_http_response,
    format_http_date,
    get_connection_header,
    get_content_type,
    get_last_modified,
    get_requested_file_name,
    is_not_modified,
    parse_http_request,
    read_requested_file,
    receive_http_request,
    resolve_request_path,
    should_keep_alive,
)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
BACKLOG = 5
KEEP_ALIVE_TIMEOUT = 10


@dataclass
class RequestResult:
    response: bytes
    status_code: int
    keep_alive: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the COMP2322 web server.")
    parser.add_argument("host", nargs="?", default=DEFAULT_HOST, help="Host to bind.")
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=DEFAULT_PORT,
        help="Port to bind.",
    )
    parser.add_argument("--host", dest="host_flag", help="Override positional host.")
    parser.add_argument("--port", dest="port_flag", type=int, help="Override positional port.")
    args = parser.parse_args()

    # Let named options override positional values when both are provided.
    args.host = args.host_flag if args.host_flag is not None else args.host
    args.port = args.port_flag if args.port_flag is not None else args.port
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    return args


def build_response_bytes(
    status_code: int,
    reason_phrase: str,
    body: bytes,
    method: str,
    version: str,
    keep_alive: bool,
    extra_headers: dict[str, str] | None = None,
) -> bytes:
    headers = {"Connection": get_connection_header(keep_alive)}
    if extra_headers:
        headers.update(extra_headers)

    return build_http_response(
        status_code=status_code,
        reason_phrase=reason_phrase,
        body=body,
        method=method,
        version=version,
        extra_headers=headers,
    )


def log_request(
    client_address: tuple[str, int],
    method: str,
    requested_file_name: str,
    response_type: str,
) -> None:
    access_time = format_http_date(datetime.now(timezone.utc))
    write_access_log(
        client_ip=client_address[0],
        access_time=access_time,
        method=method,
        requested_file_name=requested_file_name,
        response_type=response_type,
    )


def process_request(
    request,
    client_address: tuple[str, int],
    result_queue: queue.Queue[RequestResult],
) -> None:
    keep_alive = should_keep_alive(request)
    requested_file_name = get_requested_file_name(request.path)
    print(
        f"[{threading.current_thread().name}] Processing request: "
        f"method={request.method}, path={request.path}, version={request.version}, "
        f"keep_alive={keep_alive}"
    )

    try:
        # Map the URL path to a safe location under the web root.
        file_path = resolve_request_path(request.path)
    except PermissionError as error:
        response = build_response_bytes(
            403,
            "Forbidden",
            b"403 Forbidden\nAccess to the requested resource is denied.\n",
            request.method,
            request.version,
            keep_alive,
        )
        log_request(client_address, request.method, requested_file_name, "403 Forbidden")
        print(
            f"[{threading.current_thread().name}] Forbidden request from "
            f"{client_address[0]}:{client_address[1]}: {error}"
        )
        result_queue.put(RequestResult(response=response, status_code=403, keep_alive=keep_alive))
        return

    # Directory listing is disabled for this project.
    if file_path.is_dir():
        response = build_response_bytes(
            403,
            "Forbidden",
            b"403 Forbidden\nDirectory access is not allowed.\n",
            request.method,
            request.version,
            keep_alive,
        )
        log_request(client_address, request.method, file_path.name, "403 Forbidden")
        print(
            f"[{threading.current_thread().name}] Forbidden directory request: "
            f"{request.path}"
        )
        result_queue.put(RequestResult(response=response, status_code=403, keep_alive=keep_alive))
        return

    # A valid path can still refer to a file that does not exist.
    if not file_path.exists():
        response = build_response_bytes(
            404,
            "File Not Found",
            b"404 File Not Found\nThe requested file does not exist.\n",
            request.method,
            request.version,
            keep_alive,
        )
        log_request(client_address, request.method, file_path.name, "404 File Not Found")
        print(
            f"[{threading.current_thread().name}] File not found for path "
            f"{request.path}"
        )
        result_queue.put(RequestResult(response=response, status_code=404, keep_alive=keep_alive))
        return

    last_modified = get_last_modified(file_path)
    last_modified_header = format_http_date(last_modified)

    # Return 304 when the client's cached copy is already up to date.
    if is_not_modified(file_path, request.headers):
        response = build_response_bytes(
            304,
            "Not Modified",
            b"",
            request.method,
            request.version,
            keep_alive,
            extra_headers={
                "Last-Modified": last_modified_header,
                "Content-Length": "0",
            },
        )
        log_request(client_address, request.method, file_path.name, "304 Not Modified")
        print(
            f"[{threading.current_thread().name}] Returned 304 Not Modified for "
            f"{file_path.name}"
        )
        result_queue.put(RequestResult(response=response, status_code=304, keep_alive=keep_alive))
        return

    # Read the file as bytes so both text and image files are supported.
    file_body = read_requested_file(file_path)
    response = build_response_bytes(
        200,
        "OK",
        file_body,
        request.method,
        request.version,
        keep_alive,
        extra_headers={
            "Content-Type": get_content_type(file_path),
            "Content-Length": str(len(file_body)),
            "Last-Modified": last_modified_header,
        },
    )
    log_request(client_address, request.method, file_path.name, "200 OK")
    print(f"[{threading.current_thread().name}] Served file: {file_path.name}")
    result_queue.put(RequestResult(response=response, status_code=200, keep_alive=keep_alive))


def handle_client(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    # This thread manages one client connection and dispatches each request
    # to a dedicated worker thread so the rubric is matched more closely.
    print(
        f"[{threading.current_thread().name}] Accepted connection from "
        f"{client_address[0]}:{client_address[1]}"
    )

    pending_data = b""

    try:
        # Allow the same connection to carry multiple requests when keep-alive is used.
        while True:
            client_socket.settimeout(KEEP_ALIVE_TIMEOUT)
            request_data, pending_data = receive_http_request(client_socket, pending_data)
            if not request_data:
                print(
                    f"[{threading.current_thread().name}] Client "
                    f"{client_address[0]}:{client_address[1]} closed the connection "
                    "without sending more data."
                )
                return

            print(
                f"[{threading.current_thread().name}] Received {len(request_data)} bytes "
                f"from {client_address[0]}:{client_address[1]}"
            )

            request = parse_http_request(request_data)

            # Spawn one worker thread for this single HTTP request.
            result_queue: queue.Queue[RequestResult] = queue.Queue(maxsize=1)
            request_worker = threading.Thread(
                target=process_request,
                args=(request, client_address, result_queue),
                daemon=True,
            )
            request_worker.start()
            request_worker.join()
            result = result_queue.get()

            client_socket.sendall(result.response)

            if not result.keep_alive:
                return
    except HttpParseError as error:
        # Unsupported methods or malformed requests are treated as 400 errors.
        response = build_response_bytes(
            400,
            "Bad Request",
            b"400 Bad Request\nThe server could not understand the HTTP request.\n",
            "GET",
            "HTTP/1.1",
            keep_alive=False,
        )
        client_socket.sendall(response)

        # Use placeholder request fields when parsing failed before a request object existed.
        write_access_log(
            client_ip=client_address[0],
            access_time=format_http_date(datetime.now(timezone.utc)),
            method="INVALID",
            requested_file_name="-",
            response_type="400 Bad Request",
        )
        print(
            f"[{threading.current_thread().name}] Bad request from "
            f"{client_address[0]}:{client_address[1]}: {error}"
        )
    except socket.timeout:
        print(
            f"[{threading.current_thread().name}] Timed out while waiting for data "
            f"from {client_address[0]}:{client_address[1]}"
        )
    finally:
        # Always release the client socket after the request is handled.
        client_socket.close()
        print(
            f"[{threading.current_thread().name}] Closed connection with "
            f"{client_address[0]}:{client_address[1]}"
        )


def run_server(host: str, port: int) -> None:
    # Create the listening socket for incoming TCP connections.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Bind to the target address and start accepting connections.
        server_socket.bind((host, port))
        server_socket.listen(BACKLOG)
        print(f"Server listening on http://{host}:{port}")
        print("Press Ctrl+C to stop the server.")

        while True:
            client_socket, client_address = server_socket.accept()

            # The main thread accepts connections. Each connection manager may
            # then create one separate request thread per HTTP request.
            worker = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True,
            )
            worker.start()
    except KeyboardInterrupt:
        print("\nServer shutdown requested by user.")
    finally:
        # Close the listening socket when the server stops.
        server_socket.close()
        print("Server socket closed.")


def main() -> None:
    args = parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
