# COMP2322 Multi-thread Web Server

This repository contains the coursework scaffold for the COMP2322 Computer Networking project. The goal of the project is to build a multi-threaded web server in Python using basic socket programming instead of high-level web frameworks.

## Current Status

This is the initial project skeleton stage. The repository already includes the required folders, sample static files, logging location, and report materials. The HTTP server logic will be implemented step by step in later commits.

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
   ├─ report_outline.md
   └─ report_outline.pdf
```

## Directory Notes

- `server.py`: main entry point for the web server.
- `utils.py`: helper functions for HTTP parsing, MIME handling, time formatting, and path safety.
- `logger_util.py`: logging helpers for request records.
- `www/`: the web root that stores files served to clients.
- `logs/`: runtime log output directory.
- `tests/`: command examples and later verification notes.
- `report/`: report outline materials for the final submission.

## Planned Features

The final implementation will support:

- Multi-threaded request handling using Python sockets and threads
- `GET` for text files and image files
- `HEAD` requests
- Response status handling for `200`, `400`, `403`, `404`, and `304`
- `Last-Modified` and `If-Modified-Since`
- `Connection: close` and `Connection: keep-alive`
- Per-request logging to `logs/server.log`

## Sample Static Files

The `www/` folder currently includes:

- `index.html` for browser access
- `hello.txt` for text file testing
- `image.jpg` for image file testing

## Notes

- The server implementation has not been completed yet.
- The project will be developed incrementally so each stage can be committed to GitHub clearly.
