"""Stage 3 server entry point for basic HTTP request parsing.

This stage extends the socket listener from stage 2 by adding:
1. Request header reception up to the end of the HTTP header block.
2. HTTP request-line parsing.
3. Header parsing for fields such as Host and Connection.
4. Method validation for GET and HEAD.
5. A 400 Bad Request response for malformed requests.

Later stages will replace the temporary success response with real file serving.
"""

from __future__ import annotations

import argparse
import socket

from utils import HttpParseError, build_http_response, parse_http_request, receive_http_request


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
BACKLOG = 5


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the server host and port.

    The project requires support for both positional arguments and named
    options such as ``--host`` and ``--port``. Named options take priority
    when both styles are provided.
    """
    parser = argparse.ArgumentParser(
        description="Start the COMP2322 web server."
    )
    parser.add_argument("host", nargs="?", default=DEFAULT_HOST, help="Host to bind.")
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=DEFAULT_PORT,
        help="Port to bind.",
    )
    parser.add_argument(
        "--host",
        dest="host_flag",
        help="Host to bind. Overrides the positional host when provided.",
    )
    parser.add_argument(
        "--port",
        dest="port_flag",
        type=int,
        help="Port to bind. Overrides the positional port when provided.",
    )
    args = parser.parse_args()
    host = args.host_flag if args.host_flag is not None else args.host
    port = args.port_flag if args.port_flag is not None else args.port
    if not 1 <= port <= 65535:
        parser.error("port must be between 1 and 65535")
    args.host = host
    args.port = port
    return args


def handle_client(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    # Handle one client connection for the current parsing stage.

    # The server reads one HTTP request, parses it, then sends either:
    # a temporary ``200 OK`` response when the request is valid
    # a ``400 Bad Request`` response when the request is malformed
   
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

    try:
        # Avoid waiting forever if the client connects but sends nothing.
        client_socket.settimeout(5)
        request_data = receive_http_request(client_socket)

        if not request_data:
            print(
                f"Client {client_address[0]}:{client_address[1]} closed "
                "the connection without sending data."
            )
            return

        print(
            f"Received {len(request_data)} bytes from "
            f"{client_address[0]}:{client_address[1]}"
        )

        request = parse_http_request(request_data)
        print(
            "Parsed request: "
            f"method={request.method}, path={request.path}, version={request.version}"
        )

        # This is a temporary response for the parsing stage only.
        body = (
            "HTTP request parsed successfully.\n"
            f"Method: {request.method}\n"
            f"Path: {request.path}\n"
            f"Version: {request.version}\n"
        ).encode("utf-8")
        response = build_http_response(
            status_code=200,
            reason_phrase="OK",
            body=body,
            method=request.method,
        )
        client_socket.sendall(response)
    except HttpParseError as error:
        print(f"Bad request from {client_address[0]}:{client_address[1]}: {error}")
        error_body = (
            "400 Bad Request\n"
            "The server could not understand the HTTP request.\n"
        ).encode("utf-8")
        response = build_http_response(
            status_code=400,
            reason_phrase="Bad Request",
            body=error_body,
        )
        client_socket.sendall(response)
    except socket.timeout:
        print(
            f"Timed out while waiting for data from "
            f"{client_address[0]}:{client_address[1]}"
        )
    finally:
        # Close the client socket after this one-request interaction.
        client_socket.close()
        print(f"Closed connection with {client_address[0]}:{client_address[1]}")


def run_server(host: str, port: int) -> None:
    """Bind, listen, and accept client connections.

    At this project stage the server handles one HTTP request per connection.
    The implementation is still single-threaded, because the threading logic
    will be added in a later milestone.
    """
    # Create an IPv4 TCP socket for the server.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Reuse the address so restarting the server is easier during development.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # Bind the socket to the chosen host and port, then start listening.
        server_socket.bind((host, port))
        server_socket.listen(BACKLOG)
        print(f"Server listening on http://{host}:{port}")
        print("Press Ctrl+C to stop the server.")

        while True:
            # Block until a client establishes a TCP connection.
            client_socket, client_address = server_socket.accept()
            handle_client(client_socket, client_address)
    except KeyboardInterrupt:
        print("\nServer shutdown requested by user.")
    finally:
        # Always release the listening socket before the program exits.
        server_socket.close()
        print("Server socket closed.")


def main() -> None:
    """Program entry point for the current server stage."""
    args = parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
