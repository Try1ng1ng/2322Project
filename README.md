# COMP2322 Multi-thread Web Server

## Project Introduction

This project implements a multi-threaded web server in Python by using basic socket programming. The server accepts HTTP requests from browsers or command-line clients, parses the requests, loads files from the local `www/` directory, builds valid HTTP responses, and sends the responses back through TCP connections.

The implementation is built from scratch and does not use `HTTPServer`, Flask, Django, FastAPI, or other high-level web server frameworks.

## Features

- Multi-threaded server where each HTTP request is processed by a dedicated worker thread
- Support for `GET` requests for text files and image files
- Support for `HEAD` requests
- Support for these response statuses:
  - `200 OK`
  - `400 Bad Request`
  - `403 Forbidden`
  - `404 File Not Found`
  - `304 Not Modified`
- `Last-Modified` response header
- `If-Modified-Since` request header handling
- `Connection: close` and `Connection: keep-alive`
- One log line per request in `logs/server.log`

## Project Structure

    2322Project/
    ├─ server.py
    ├─ utils.py
    ├─ logger_util.py
    ├─ README.md
    ├─ www/
    │  ├─ index.html
    │  ├─ hello.txt
    │  └─ image.jpg
    ├─ logs/
    │  └─ server.log
    ├─ tests/
    │  ├─ curl_examples.txt
    │  └─ keep_alive_client.py
    └─ report/

## Environment Requirements

- Python 3.10 or above is recommended
- Standard library only
- Tested on Windows PowerShell

## How To Run

Run with the default host and port:

    python server.py

Run with positional arguments:

    python server.py 127.0.0.1 8080

Run with named arguments:

    python server.py --host 127.0.0.1 --port 8080

Default settings:

- Host: `127.0.0.1`
- Port: `8080`

## How To Use

After the server starts, open a browser or another terminal and send HTTP requests to:

    http://127.0.0.1:8080

The server root directory is `www/`. All accessible files are served from that folder.

## Browser Examples

Open these addresses in a browser:

- `http://127.0.0.1:8080/`
- `http://127.0.0.1:8080/hello.txt`
- `http://127.0.0.1:8080/image.jpg`

## curl Test Commands

Use `curl.exe` in PowerShell to avoid the built-in `curl` alias.

### 1. GET text file -> 200 OK

    curl.exe -v http://127.0.0.1:8080/hello.txt

### 2. GET image file -> 200 OK

    curl.exe -o downloaded.jpg http://127.0.0.1:8080/image.jpg

### 3. HEAD request -> 200 OK

    curl.exe -I http://127.0.0.1:8080/hello.txt

### 4. Missing file -> 404 File Not Found

    curl.exe -v http://127.0.0.1:8080/notfound.txt

### 5. Forbidden path -> 403 Forbidden

    curl.exe --path-as-is -v http://127.0.0.1:8080/../server.py

### 6. Bad request -> 400 Bad Request

    curl.exe -v -X POST http://127.0.0.1:8080/

### 7. Get Last-Modified

    curl.exe -I http://127.0.0.1:8080/hello.txt

### 8. If-Modified-Since -> 304 Not Modified

Copy the `Last-Modified` value from the previous command and run:

    curl.exe -v -H "If-Modified-Since: <Last-Modified value>" http://127.0.0.1:8080/hello.txt

### 9. Connection: close

    curl.exe -v -H "Connection: close" http://127.0.0.1:8080/hello.txt

### 10. Connection: keep-alive

    curl.exe -v -H "Connection: keep-alive" http://127.0.0.1:8080/hello.txt

### 11. Keep-alive test with one socket

    python .\tests\keep_alive_client.py

## Log File

The server writes access logs to:

    logs/server.log

Each request creates one log line. The log format includes:

- client IP address
- access time
- request method
- request path
- HTTP version
- response status code

Example:

    127.0.0.1 | Mon, 14 Apr 2026 08:30:00 GMT | GET /hello.txt HTTP/1.1 | 200

## Notes

- The server only serves files inside `www/`
- Directory listing is disabled
- Path traversal attempts return `403 Forbidden`
- `HEAD` responses do not include a body
- `304 Not Modified` responses do not include a body
- For PowerShell testing, prefer `curl.exe` instead of `curl`
- If `server.log` looks empty, stop the running server and restart it before testing again
- The server uses a connection-handling thread plus one request worker thread for each HTTP request on that connection
