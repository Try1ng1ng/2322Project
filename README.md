# COMP2322 Multi-thread Web Server

This repository contains the coursework project for the COMP2322 Computer Networking module. The goal is to build a multi-threaded web server in Python using basic socket programming instead of high-level web frameworks.

## Current Status

The project now includes the stage 6 caching prototype. At this point, the program can:

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

Persistent connections and logging will be added in later commits.

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

## Stage 6 Test Examples

Use `curl.exe` in PowerShell to avoid the `curl` alias issue.

```bash
curl.exe -I http://127.0.0.1:8080/hello.txt
curl.exe -v -H "If-Modified-Since: Mon, 13 Apr 2026 07:00:00 GMT" http://127.0.0.1:8080/hello.txt
curl.exe --path-as-is -v http://127.0.0.1:8080/../server.py
curl.exe -v http://127.0.0.1:8080/notfound.txt
curl.exe -v -X POST http://127.0.0.1:8080/
```

To test `304 Not Modified`:

1. Run `curl.exe -I http://127.0.0.1:8080/hello.txt`
2. Copy the `Last-Modified` value from the response
3. Send a second request with:

```bash
curl.exe -v -H "If-Modified-Since: <copied Last-Modified value>" http://127.0.0.1:8080/hello.txt
```

If the file has not changed, the server should return `304 Not Modified` without a body.

## Notes

- The web root is the `www/` directory.
- Directory listing is disabled and returns `403 Forbidden`.
- Each client connection is handled by a dedicated worker thread.
- Existing files now include the `Last-Modified` response header.
