"""Basic server startup for the COMP2322 multi-thread web server project.

This stage focuses on the foundational networking workflow:
1. Parse the host and port from the command line.
2. Create a TCP socket.
3. Bind the socket to the requested address.
4. Listen for incoming client connections.
5. Accept one connection at a time and read incoming data.

Later stages will extend this file into a full HTTP web server.
"""

from __future__ import annotations

import argparse
import socket


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
BACKLOG = 5
BUFFER_SIZE = 1024


def parse_args() -> argparse.Namespace:

    #Parse command-line arguments for the server host and port.
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


def run_server(host: str, port: int) -> None:
    #Bind, listen, and accept client connections.


    
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
            print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
            try:
                # Avoid waiting forever if the client connects but sends nothing.
                client_socket.settimeout(5)
                # Read a small amount of data just to confirm the socket works.
                data = client_socket.recv(BUFFER_SIZE)
                if data:
                    print(
                        f"Received {len(data)} bytes from "
                        f"{client_address[0]}:{client_address[1]}"
                    )
                else:
                    print(
                        f"Client {client_address[0]}:{client_address[1]} closed "
                        "the connection without sending data."
                    )
            except socket.timeout:
                print(
                    f"Timed out while waiting for data from "
                    f"{client_address[0]}:{client_address[1]}"
                )
            finally:
                # Close the client socket after this simple one-shot interaction.
                client_socket.close()
                print(
                    f"Closed connection with {client_address[0]}:{client_address[1]}"
                )
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
