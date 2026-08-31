from __future__ import annotations

import html
import socket
import threading
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from .books import Book, save_uploaded_book


class UploadServer:
    def __init__(self, upload_dir: Path, port: int, on_book_uploaded: Callable[[Book], None]) -> None:
        self.upload_dir = upload_dir
        self.on_book_uploaded = on_book_uploaded
        self.server = ThreadingHTTPServer(("0.0.0.0", port), self._handler_class())
        self.thread = threading.Thread(target=self.server.serve_forever, name="ereader-upload-server", daemon=True)

    @property
    def port(self) -> int:
        return int(self.server.server_address[1])

    @property
    def url(self) -> str:
        return f"http://{local_ip()}:{self.port}"

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        upload_dir = self.upload_dir
        on_book_uploaded = self.on_book_uploaded

        class UploadHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path not in {"/", "/upload"}:
                    self.send_error(404)
                    return

                self._send_html(_upload_form_html())

            def do_POST(self) -> None:
                if self.path != "/upload":
                    self.send_error(404)
                    return

                length = int(self.headers.get("Content-Length", "0"))
                content_type = self.headers.get("Content-Type", "")
                body = self.rfile.read(length)
                filename, content = _parse_multipart_upload(content_type, body)
                if not filename or content is None:
                    self._send_html(_upload_form_html("Choose a .txt file first."), status=400)
                    return

                if not filename.lower().endswith(".txt"):
                    self._send_html(_upload_form_html("Only .txt files are supported."), status=400)
                    return

                book = save_uploaded_book(upload_dir, filename, content)
                on_book_uploaded(book)
                message = f"Uploaded {html.escape(book.title)}. You can return to the reader now."
                self._send_html(_upload_form_html(message))

            def log_message(self, format: str, *args: object) -> None:
                return

            def _send_html(self, page: str, status: int = 200) -> None:
                encoded = page.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return UploadHandler


def local_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return socket.gethostbyname(socket.gethostname())


def _parse_multipart_upload(content_type: str, body: bytes) -> tuple[str | None, bytes | None]:
    if "multipart/form-data" not in content_type:
        return None, None

    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
    )
    for part in message.iter_parts():
        if part.get_param("name", header="content-disposition") != "book":
            continue

        filename = part.get_filename()
        payload = part.get_payload(decode=True)
        return filename, payload

    return None, None


def _upload_form_html(message: str = "") -> str:
    escaped_message = html.escape(message)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EReader Upload</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 34rem; }}
    form {{ display: grid; gap: 1rem; margin-top: 1.5rem; }}
    button {{ font: inherit; padding: 0.8rem 1rem; }}
    input {{ font: inherit; }}
    .message {{ margin-top: 1rem; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>EReader Upload</h1>
  <p>Upload a UTF-8 text file and it will appear in the reader library.</p>
  <form action="/upload" method="post" enctype="multipart/form-data">
    <input type="file" name="book" accept=".txt,text/plain" required>
    <button type="submit">Upload text file</button>
  </form>
  <p class="message">{escaped_message}</p>
</body>
</html>"""
