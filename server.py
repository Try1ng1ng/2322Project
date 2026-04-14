from __future__ import annotations

import argparse
import socket
import threading
from datetime import datetime, timezone

from logger_util import write_access_log
from utils import (
    HttpParseError,
    build_http_response,
    format_http_date,
    get_connection_header,
    get_content_type,
    get_last_modified,
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


def send_simple_response(
    client_socket: socket.socket,
    status_code: int,
    reason_phrase: str,
    body: bytes,
    method: str,
    keep_alive: bool,
    extra_headers: dict[str, str] | None = None,
) -> None:
    headers = {"Connection": get_connection_header(keep_alive)}
    if extra_headers:
        headers.update(extra_headers)

    response = build_http_response(
        status_code=status_code,
        reason_phrase=reason_phrase,
        body=body,
        method=method,
        extra_headers=headers,
    )
    client_socket.sendall(response)


def log_request(
    client_address: tuple[str, int],
    request,
    status_code: int,
) -> None:
    access_time = format_http_date(datetime.now(timezone.utc))
    write_access_log(
        client_ip=client_address[0],
        access_time=access_time,
        method=request.method,
        path=request.path,
        version=request.version,
        status_code=status_code,
    )


def handle_client(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    # Each worker thread handles one client connection from start to finish.
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
            keep_alive = should_keep_alive(request)
            print(
                f"[{threading.current_thread().name}] Parsed request: "
                f"method={request.method}, path={request.path}, version={request.version}, "
                f"keep_alive={keep_alive}"
            )

            try:
                # Map the URL path to a safe location under the web root.
                file_path = resolve_request_path(request.path)
            except PermissionError as error:
                body = b"403 Forbidden\nAccess to the requested resource is denied.\n"
                send_simple_response(
                    client_socket,
                    403,
                    "Forbidden",
                    body,
                    request.method,
                    keep_alive,
                )
                log_request(client_address, request, 403)
                print(
                    f"[{threading.current_thread().name}] Forbidden request from "
                    f"{client_address[0]}:{client_address[1]}: {error}"
                )
                if not keep_alive:
                    return
                continue

            # Directory listing is disabled for this project.
            if file_path.is_dir():
                body = b"403 Forbidden\nDirectory access is not allowed.\n"
                send_simple_response(
                    client_socket,
                    403,
                    "Forbidden",
                    body,
                    request.method,
                    keep_alive,
                )
                log_request(client_address, request, 403)
                print(
                    f"[{threading.current_thread().name}] Forbidden directory request: "
                    f"{request.path}"
                )
                if not keep_alive:
                    return
                continue

            # A valid path can still refer to a file that does not exist.
            if not file_path.exists():
                body = b"404 File Not Found\nThe requested file does not exist.\n"
                send_simple_response(
                    client_socket,
                    404,
                    "File Not Found",
                    body,
                    request.method,
                    keep_alive,
                )
                log_request(client_address, request, 404)
                print(
                    f"[{threading.current_thread().name}] File not found for path "
                    f"{request.path}"
                )
                if not keep_alive:
                    return
                continue

            last_modified = get_last_modified(file_path)
            last_modified_header = format_http_date(last_modified)

            # Return 304 when the client's cached copy is already up to date.
            if is_not_modified(file_path, request.headers):
                send_simple_response(
                    client_socket,
                    304,
                    "Not Modified",
                    b"",
                    request.method,
                    keep_alive,
                    extra_headers={
                        "Last-Modified": last_modified_header,
                        "Content-Length": "0",
                    },
                )
                log_request(client_address, request, 304)
                print(
                    f"[{threading.current_thread().name}] Returned 304 Not Modified for "
                    f"{file_path.name}"
                )
                if not keep_alive:
                    return
                continue

            # Read the file as bytes so both text and image files are supported.
            file_body = read_requested_file(file_path)
            send_simple_response(
                client_socket,
                200,
                "OK",
                file_body,
                request.method,
                keep_alive,
                extra_headers={
                    "Content-Type": get_content_type(file_path),
                    "Content-Length": str(len(file_body)),
                    "Last-Modified": last_modified_header,
                },
            )
            log_request(client_address, request, 200)
            print(f"[{threading.current_thread().name}] Served file: {file_path.name}")

            if not keep_alive:
                return
    except HttpParseError as error:
        # Unsupported methods or malformed requests are treated as 400 errors.
        send_simple_response(
            client_socket,
            400,
            "Bad Request",
            b"400 Bad Request\nThe server could not understand the HTTP request.\n",
            "GET",
            keep_alive=False,
        )
        # Use placeholder request fields when parsing failed before a request object existed.
        write_access_log(
            client_ip=client_address[0],
            access_time=format_http_date(datetime.now(timezone.utc)),
            method="INVALID",
            path="-",
            version="-",
            status_code=400,
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

            # The main thread keeps accepting new clients while worker threads
            # process individual connections in parallel.
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
