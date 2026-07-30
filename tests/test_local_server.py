from __future__ import annotations

import http.client
import importlib
import pathlib
import sys
import tempfile
import unittest
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
RUNTIME = PLUGIN_ROOT / "divan_runtime"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


def load_server():
    if not (RUNTIME / "local_server.py").is_file():
        raise AssertionError("local_server.py is missing")
    return importlib.import_module("divan_runtime.local_server")


def request(
    session,
    path: str,
    *,
    method: str = "GET",
    token: str | None = None,
    host: str | None = None,
    etag: str | None = None,
):
    parsed = urllib.parse.urlsplit(session.url)
    connection = http.client.HTTPConnection("127.0.0.1", parsed.port, timeout=3)
    connection.putrequest(method, path, skip_host=True)
    connection.putheader(
        "Host",
        host if host is not None else f"127.0.0.1:{parsed.port}",
    )
    if token is not None:
        connection.putheader("X-Divan-Session", token)
    if etag is not None:
        connection.putheader("If-None-Match", etag)
    connection.endheaders()
    response = connection.getresponse()
    body = response.read()
    result = response.status, dict(response.getheaders()), body
    connection.close()
    return result


class LocalServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="divan-server-")
        self.project = pathlib.Path(self.temporary.name)
        self.module = load_server()
        self.session = self.module.start_server(
            self.project,
            "en",
            idle_timeout=5,
        )

    def tearDown(self) -> None:
        self.session.close()
        self.temporary.cleanup()

    def test_server_uses_loopback_ephemeral_port_and_fragment_token(self) -> None:
        parsed = urllib.parse.urlsplit(self.session.url)

        self.assertEqual(parsed.hostname, "127.0.0.1")
        self.assertGreater(parsed.port or 0, 0)
        self.assertEqual(parsed.fragment, self.session.token)
        self.assertNotIn(self.session.token, parsed.path)
        self.assertFalse(parsed.query)
        self.assertEqual(parsed.path, "/session/")

    def test_status_requires_session_header_and_returns_secure_json(self) -> None:
        status, _, _ = request(self.session, "/api/status")
        self.assertEqual(status, 401)

        status, headers, body = request(
            self.session,
            "/api/status",
            token=self.session.token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertIn(b'"schema_version": 1', body)

    def test_etag_returns_not_modified_for_unchanged_snapshot(self) -> None:
        status, headers, _ = request(
            self.session,
            "/api/status",
            token=self.session.token,
        )
        self.assertEqual(status, 200)
        etag = headers["ETag"]

        status, _, body = request(
            self.session,
            "/api/status",
            token=self.session.token,
            etag=etag,
        )
        self.assertEqual(status, 304)
        self.assertEqual(body, b"")

    def test_host_header_mutation_and_traversal_fail_closed(self) -> None:
        self.assertEqual(
            request(
                self.session,
                "/api/status",
                token=self.session.token,
                host="attacker.example",
            )[0],
            421,
        )
        self.assertEqual(
            request(
                self.session,
                "/api/status",
                method="POST",
                token=self.session.token,
            )[0],
            405,
        )
        self.assertEqual(request(self.session, "/../secrets")[0], 404)
        self.assertEqual(request(self.session, "/%2e%2e/secrets")[0], 404)

    def test_close_stops_the_server_thread(self) -> None:
        self.session.close()

        self.assertFalse(self.session.thread.is_alive())
        self.session.close()


if __name__ == "__main__":
    unittest.main()
