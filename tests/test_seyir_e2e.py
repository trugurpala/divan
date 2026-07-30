from __future__ import annotations

import http.client
import json
import pathlib
import sys
import tempfile
import unittest
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "sadrazam"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from divan_runtime import local_server  # noqa: E402


def get(session, path: str, *, token: str | None = None):
    parsed = urllib.parse.urlsplit(session.url)
    connection = http.client.HTTPConnection("127.0.0.1", parsed.port, timeout=3)
    headers = {"Host": f"127.0.0.1:{parsed.port}"}
    if token is not None:
        headers["X-Divan-Session"] = token
    connection.request("GET", path, headers=headers)
    response = connection.getresponse()
    body = response.read()
    result = response.status, dict(response.getheaders()), body
    connection.close()
    return result


class SeyirEndToEndTests(unittest.TestCase):
    def test_live_session_serves_ui_assets_and_localized_status(self) -> None:
        with tempfile.TemporaryDirectory(prefix="divan-seyir-e2e-") as temporary:
            session = local_server.start_server(
                pathlib.Path(temporary),
                "tr",
                idle_timeout=10,
            )
            self.addCleanup(session.close)

            html_status, _, html = get(session, "/session/")
            css_status, _, css = get(session, "/session/studio.css")
            js_status, _, script = get(session, "/session/studio.js")
            api_status, headers, body = get(
                session,
                "/api/status",
                token=session.token,
            )

        self.assertEqual(html_status, 200)
        self.assertEqual(css_status, 200)
        self.assertEqual(js_status, 200)
        self.assertIn(b"Divan Seyir", html)
        self.assertIn(b"prefers-reduced-motion", css)
        self.assertIn(b"X-Divan-Session", script)
        self.assertEqual(api_status, 200)
        self.assertIn("no-store", headers["Cache-Control"])
        payload = json.loads(body)
        self.assertEqual(payload["locale"], "tr")
        self.assertEqual(payload["copy"]["connection.connected"], "Bağlandı")
        self.assertEqual(payload["goal"]["status"], "NO_ACTIVE_GOAL")


if __name__ == "__main__":
    unittest.main()
