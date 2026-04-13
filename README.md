# COMP2322 Multi-thread Web Server

This repository contains the coursework project for the COMP2322 Computer Networking module. The goal is to build a multi-threaded web server in Python using basic socket programming instead of high-level web frameworks.

## Current Status

The project now includes the stage 7 connection-management prototype. At this point, the program can:

- parse command-line host and port arguments
- create a TCP socket
- bind and listen on the requested address
- parse `GET` and `HEAD` requests
- serve files from `www/`
- return text files and image files
- return `200 OK`, `400 Bad Request`, `403 Forbidden`, `404 File Not Found`, and `304 Not Modified`
- create a separate thread for each client connection
- send `Last-Modified`
- process `If-Modified-Since`
- handle `Connection: close`
- handle `Connection: keep-alive`

Logging will be added in a later commit.

## Project Structure

```text
2322Project/
├─ server.py
├─ utils.py
├─ logger_util.py
├─ www/
│  ├─ index.html
│  ├─ hello.txt
│  └─ image.jpg
├─ logs/
│  └─ server.log
├─ tests/
│  └─ curl_examples.txt
├─ README.md
└─ report/
   └─ report_outline.md
```

## Run The Current Stage

Start the server:

```bash
python server.py
```

Or specify host and port:

```bash
python server.py --host 127.0.0.1 --port 8080
```

## Stage 7 Test Examples

Use `curl.exe` in PowerShell to avoid the `curl` alias issue.

```bash
curl.exe -v -H "Connection: close" http://127.0.0.1:8080/hello.txt
curl.exe -v -H "Connection: keep-alive" http://127.0.0.1:8080/hello.txt
curl.exe -I http://127.0.0.1:8080/hello.txt
curl.exe -v http://127.0.0.1:8080/notfound.txt
curl.exe --path-as-is -v http://127.0.0.1:8080/../server.py
curl.exe -v -X POST http://127.0.0.1:8080/
```

To demonstrate a persistent connection more clearly, use a client that can send two HTTP requests over the same socket and confirm that the server thread handles both requests before the connection closes.

## Notes

- The web root is the `www/` directory.
- Directory listing is disabled and returns `403 Forbidden`.
- Each client connection is handled by a dedicated worker thread.
- Existing files include the `Last-Modified` response header.
- The server now keeps a connection open when the request asks for `keep-alive`.
