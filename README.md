# COMP2322 Multi-thread Web Server

This repository contains the coursework project for the COMP2322 Computer Networking module. The goal is to build a multi-threaded web server in Python using basic socket programming instead of high-level web frameworks.

## Current Status

The project now includes the stage 3 parsing prototype. At this point, the program can:

- parse command-line host and port arguments
- create a TCP socket
- bind and listen on the requested address
- accept one client connection at a time
- read the HTTP header section from the socket
- parse the request line and request headers
- accept `GET` and `HEAD`
- return `400 Bad Request` for malformed requests
- return a temporary `200 OK` text response for valid requests

Real file serving, multi-threading, `403`, `404`, `304`, logging, and persistent connections will be added in later commits.

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

## Directory Notes

- `server.py`: main entry point for the web server.
- `utils.py`: helper functions for HTTP parsing, response formatting, and later file/path handling.
- `logger_util.py`: logging helpers for request records.
- `www/`: the web root that stores files served to clients.
- `logs/`: runtime log output directory.
- `tests/`: command examples and later verification notes.
- `report/`: report outline materials for the final submission.

## Planned Features

The final implementation will support:

- multi-threaded request handling using Python sockets and threads
- `GET` for text files and image files
- `HEAD` requests
- response status handling for `200`, `400`, `403`, `404`, and `304`
- `Last-Modified` and `If-Modified-Since`
- `Connection: close` and `Connection: keep-alive`
- per-request logging to `logs/server.log`

## Run The Current Stage

Start the server with the default host and port:

```bash
python server.py
```

Start the server with positional arguments:

```bash
python server.py 127.0.0.1 8080
```

Start the server with named arguments:

```bash
python server.py --host 127.0.0.1 --port 8080
```

After the server starts, open a separate terminal and test the parsing stage with `curl`.

Valid request example:

```bash
curl -v http://127.0.0.1:8080/
```

Valid `HEAD` example:

```bash
curl -I http://127.0.0.1:8080/
```

Bad request example using an unsupported method:

```bash
curl -v -X POST http://127.0.0.1:8080/
```

At this stage, a valid request only receives a temporary success response showing the parsed request details. Real static file responses will be added later.

## Sample Static Files

The `www/` folder currently includes:

- `index.html` for browser access
- `hello.txt` for text file testing
- `image.jpg` for image file testing

## Notes

- The full HTTP server implementation has not been completed yet.
- The project will be developed incrementally so each stage can be committed to GitHub clearly.
