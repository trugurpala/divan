"""Loopback-only, read-only HTTP presentation for Divan Seyir."""

from __future__ import annotations

import dataclasses
import http.server
import json
import pathlib
import secrets
import threading
import time
import urllib.parse
import webbrowser
from typing import Any

from . import locales, status

HOST = "127.0.0.1"
SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self'; font-src 'self'; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}
ASSETS = {
    "/session/": ("index.html", "text/html; charset=utf-8"),
    "/session/studio.css": ("studio.css", "text/css; charset=utf-8"),
    "/session/studio.js": ("studio.js", "text/javascript; charset=utf-8"),
}


class _SeyirServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(
        self,
        address: tuple[str, int],
        handler: type[http.server.BaseHTTPRequestHandler],
        *,
        project: pathlib.Path,
        language: str,
        token: str,
        idle_timeout: float,
    ) -> None:
        super().__init__(address, handler)
        self.project = project
        self.language = language
        self.token = token
        self.idle_timeout = idle_timeout
        self.last_activity = time.monotonic()
        self.expected_host = f"{HOST}:{self.server_address[1]}"

    def touch(self) -> None:
        self.last_activity = time.monotonic()


class _Handler(http.server.BaseHTTPRequestHandler):
    server: _SeyirServer
    protocol_version = "HTTP/1.1"
    server_version = "DivanSeyir"
    sys_version = ""

    def log_message(self, format: str, *args: Any) -> None:
        del format, args

    def _headers(
        self,
        status_code: int,
        content_type: str,
        content_length: int,
        *,
        etag: str | None = None,
    ) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        if etag is not None:
            self.send_header("ETag", etag)
        self.end_headers()

    def _send(
        self,
        status_code: int,
        body: bytes = b"",
        *,
        content_type: str = "text/plain; charset=utf-8",
        etag: str | None = None,
    ) -> None:
        self._headers(
            status_code,
            content_type,
            len(body),
            etag=etag,
        )
        if self.command != "HEAD" and body:
            self.wfile.write(body)

    def _valid_host(self) -> bool:
        return self.headers.get("Host", "") == self.server.expected_host

    def _decoded_path(self) -> str | None:
        raw_path = urllib.parse.urlsplit(self.path).path
        try:
            decoded = urllib.parse.unquote(raw_path, errors="strict")
        except UnicodeError:
            return None
        if "\\" in decoded:
            return None
        parts = pathlib.PurePosixPath(decoded).parts
        if ".." in parts or "." in parts[1:]:
            return None
        return decoded

    def _authorized(self) -> bool:
        observed = self.headers.get("X-Divan-Session", "")
        return secrets.compare_digest(observed, self.server.token)

    def _status(self) -> None:
        if not self._authorized():
            self._send(401, b"Unauthorized\n")
            return
        snapshot = status.build_snapshot(
            self.server.project,
            self.server.language,
        )
        etag = f'"{status.snapshot_etag(snapshot)}"'
        if self.headers.get("If-None-Match") == etag:
            self._send(304, etag=etag)
            return
        body = (
            json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
        self._send(
            200,
            body,
            content_type="application/json; charset=utf-8",
            etag=etag,
        )

    def _asset(self, path: str) -> None:
        asset = ASSETS.get(path)
        if asset is None:
            self._send(404, b"Not found\n")
            return
        name, content_type = asset
        candidate = pathlib.Path(__file__).resolve().parent / "studio" / name
        try:
            body = candidate.read_bytes()
        except OSError:
            self._send(404, b"Not found\n")
            return
        self._send(200, body, content_type=content_type)

    def _read(self) -> None:
        self.server.touch()
        if not self._valid_host():
            self._send(421, b"Misdirected request\n")
            return
        path = self._decoded_path()
        if path is None:
            self._send(404, b"Not found\n")
            return
        if path == "/api/status":
            self._status()
            return
        self._asset(path)

    def do_GET(self) -> None:  # noqa: N802
        self._read()

    def do_HEAD(self) -> None:  # noqa: N802
        self._read()

    def _reject_mutation(self) -> None:
        self.server.touch()
        if not self._valid_host():
            self._send(421, b"Misdirected request\n")
            return
        self._send(405, b"Method not allowed\n")

    do_POST = _reject_mutation
    do_PUT = _reject_mutation
    do_PATCH = _reject_mutation
    do_DELETE = _reject_mutation
    do_OPTIONS = _reject_mutation
    do_TRACE = _reject_mutation
    do_CONNECT = _reject_mutation


@dataclasses.dataclass
class ServerSession:
    """One temporary local Seyir session."""

    server: _SeyirServer
    thread: threading.Thread
    url: str
    token: str
    _closed: threading.Event = dataclasses.field(default_factory=threading.Event)
    _close_lock: threading.Lock = dataclasses.field(default_factory=threading.Lock)

    def close(self) -> None:
        """Stop the server exactly once and wait for its worker to exit."""
        with self._close_lock:
            if self._closed.is_set():
                return
            self._closed.set()
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not threading.current_thread():
            self.thread.join(timeout=5)


def _idle_watch(session: ServerSession) -> None:
    interval = min(max(session.server.idle_timeout / 10, 0.05), 1.0)
    while not session._closed.wait(interval):
        if time.monotonic() - session.server.last_activity >= session.server.idle_timeout:
            session.close()
            return


def start_server(
    project: pathlib.Path,
    language: str,
    idle_timeout: float = 1800.0,
) -> ServerSession:
    """Start a protected loopback session on an OS-selected free port."""
    root = pathlib.Path(project).resolve()
    if not root.is_dir():
        raise ValueError(f"project directory does not exist: {root}")
    if idle_timeout <= 0:
        raise ValueError("idle timeout must be positive")
    resolved_language = locales.resolve_language(language)
    token = secrets.token_urlsafe(32)
    server = _SeyirServer(
        (HOST, 0),
        _Handler,
        project=root,
        language=resolved_language,
        token=token,
        idle_timeout=idle_timeout,
    )
    thread = threading.Thread(
        target=server.serve_forever,
        name="divan-seyir",
        daemon=True,
    )
    session = ServerSession(
        server=server,
        thread=thread,
        url=(
            f"http://{HOST}:{server.server_address[1]}"
            f"/session/#{token}"
        ),
        token=token,
    )
    thread.start()
    threading.Thread(
        target=_idle_watch,
        args=(session,),
        name="divan-seyir-idle",
        daemon=True,
    ).start()
    return session


def serve(
    project: pathlib.Path,
    language: str,
    open_browser: bool,
) -> int:
    """Serve Seyir until interrupted or the idle limit closes the session."""
    session = start_server(project, language)
    catalog = locales.load_messages(pathlib.Path(__file__).resolve().parent)
    print(session.url, flush=True)
    print(
        locales.message(catalog, "server.stop", session.server.language),
        flush=True,
    )
    if open_browser:
        webbrowser.open(session.url, new=2)
    try:
        session.thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        session.close()
    return 0
