from __future__ import annotations

import html
import socket
import threading
import zipfile
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs

from .books import Book, list_uploaded_entries, load_uploaded_books, save_uploaded_book, update_book_metadata


class UploadServer:
    def __init__(self, upload_dir: Path, port: int, on_library_changed: Callable[[list[Book]], None]) -> None:
        self.upload_dir = upload_dir
        self.on_library_changed = on_library_changed
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
        on_library_changed = self.on_library_changed

        class UploadHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path not in {"/", "/upload", "/manage"}:
                    self.send_error(404)
                    return

                self._send_html(_library_manager_html(upload_dir))

            def do_POST(self) -> None:
                if self.path == "/upload":
                    self._handle_upload()
                elif self.path == "/manage":
                    self._handle_manage()
                else:
                    self.send_error(404)
                    return

            def _handle_upload(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                content_type = self.headers.get("Content-Type", "")
                body = self.rfile.read(length)
                filename, content = _parse_multipart_upload(content_type, body)
                if not filename or content is None:
                    self._send_html(_library_manager_html(upload_dir, "Choose a .txt or .epub file first."), status=400)
                    return

                if Path(filename).suffix.lower() not in {".txt", ".epub"}:
                    self._send_html(_library_manager_html(upload_dir, "Only .txt and .epub files are supported."), status=400)
                    return

                try:
                    book = save_uploaded_book(upload_dir, filename, content)
                except (KeyError, OSError, ValueError, zipfile.BadZipFile):
                    self._send_html(_library_manager_html(upload_dir, "That EPUB could not be read."), status=400)
                    return
                on_library_changed(load_uploaded_books(upload_dir))
                message = f"Uploaded {html.escape(book.title)}. You can return to the reader now."
                self._send_html(_library_manager_html(upload_dir, message))

            def _handle_manage(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length).decode("utf-8", errors="replace")
                form = parse_qs(body, keep_blank_values=True)
                filenames = form.get("filename", [])
                titles = form.get("title", [])
                authors = form.get("author", [])

                try:
                    for filename, title, author in zip(filenames, titles, authors):
                        update_book_metadata(upload_dir, filename, title, author)
                except FileNotFoundError:
                    self._send_html(_library_manager_html(upload_dir, "One book could not be found."), status=400)
                    return

                on_library_changed(load_uploaded_books(upload_dir))
                self._send_html(_library_manager_html(upload_dir, "Saved library changes."))

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


def _library_manager_html(upload_dir: Path, message: str = "") -> str:
    escaped_message = html.escape(message)
    entries = list_uploaded_entries(upload_dir)
    rows = "\n".join(
        f"""
      <tr>
        <td>
          <input type="hidden" name="filename" value="{html.escape(entry.filename)}">
          <span class="filename">{html.escape(entry.filename)}</span>
        </td>
        <td><input name="title" value="{html.escape(entry.title)}"></td>
        <td><input name="author" value="{html.escape(entry.author)}"></td>
      </tr>"""
        for entry in entries
    )
    if not rows:
        rows = '<tr><td colspan="3" class="empty">No uploaded books yet.</td></tr>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EReader Library Manager</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 58rem; }}
    h1, h2 {{ margin: 0 0 1rem; }}
    section {{ border-top: 1px solid #d0d0d0; padding: 1.5rem 0; }}
    form.upload {{ display: grid; gap: 1rem; max-width: 34rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th {{ font-size: 0.85rem; text-align: left; color: #555; }}
    th, td {{ border-bottom: 1px solid #ddd; padding: 0.7rem 0.5rem; vertical-align: middle; }}
    input {{ box-sizing: border-box; font: inherit; padding: 0.55rem; width: 100%; }}
    button {{ font: inherit; padding: 0.75rem 1rem; }}
    .filename {{ color: #555; font-size: 0.9rem; overflow-wrap: anywhere; }}
    .message {{ margin-top: 1rem; font-weight: 700; }}
    .empty {{ color: #666; padding: 1rem 0.5rem; }}
    .actions {{ margin-top: 1rem; }}
  </style>
</head>
<body>
  <h1>Library Manager</h1>
  <p class="message">{escaped_message}</p>
  <section>
    <h2>Add Book</h2>
    <form class="upload" action="/upload" method="post" enctype="multipart/form-data">
      <input type="file" name="book" accept=".txt,.epub,text/plain,application/epub+zip" required>
      <button type="submit">Upload book</button>
    </form>
  </section>
  <section>
    <h2>Books</h2>
    <form action="/manage" method="post">
      <table>
        <thead>
          <tr><th>File</th><th>Title</th><th>Author</th></tr>
        </thead>
        <tbody>{rows}
        </tbody>
      </table>
      <div class="actions"><button type="submit">Save changes</button></div>
    </form>
  </section>
</body>
</html>"""
