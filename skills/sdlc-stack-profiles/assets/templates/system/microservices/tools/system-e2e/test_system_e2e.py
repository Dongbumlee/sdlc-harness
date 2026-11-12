import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

import system_e2e


def make_map(root: Path, *, with_pact: bool = True) -> Path:
    if with_pact:
        pact = root / "contracts" / "items-api.pact.json"
        pact.parent.mkdir(parents=True, exist_ok=True)
        pact.write_text("{}", encoding="utf-8")
    data = {
        "system": "Sample",
        "services": [
            {"name": "items-api", "port": 8081, "health": "/health"},
            {"name": "catalog-api", "port": 8082, "health": "/health"},
        ],
        "boundaries": [
            {
                "name": "catalog-reads-items",
                "consumer": "catalog-api",
                "provider": "items-api",
                "pact": "contracts/items-api.pact.json",
            }
        ],
    }
    path = root / "system.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        body = b'{"status": "ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class SystemE2ETest(unittest.TestCase):
    def test_check_mode_passes_with_pact_present(self):
        with TemporaryDirectory() as tmp:
            path = make_map(Path(tmp))
            code = system_e2e.main(["--map", str(path), "--check"])
            self.assertEqual(code, 0)

    def test_check_mode_fails_without_pact_file(self):
        with TemporaryDirectory() as tmp:
            path = make_map(Path(tmp), with_pact=False)
            code = system_e2e.main(["--map", str(path), "--check"])
            self.assertEqual(code, 1)

    def test_boundary_with_unknown_service_fails(self):
        with TemporaryDirectory() as tmp:
            path = make_map(Path(tmp))
            data = json.loads(path.read_text(encoding="utf-8"))
            data["boundaries"][0]["consumer"] = "ghost-api"
            path.write_text(json.dumps(data), encoding="utf-8")
            code = system_e2e.main(["--map", str(path), "--check"])
            self.assertEqual(code, 1)

    def test_probe_passes_against_a_healthy_service(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with TemporaryDirectory() as tmp:
                path = make_map(Path(tmp))
                base = f"http://127.0.0.1:{server.server_port}"
                code = system_e2e.main(
                    [
                        "--map",
                        str(path),
                        "--base",
                        f"items-api={base}",
                        "--base",
                        f"catalog-api={base}",
                    ]
                )
                self.assertEqual(code, 0)
        finally:
            server.shutdown()

    def test_probe_fails_against_a_dead_service(self):
        with TemporaryDirectory() as tmp:
            path = make_map(Path(tmp))
            code = system_e2e.main(
                [
                    "--map",
                    str(path),
                    "--base",
                    "items-api=http://127.0.0.1:1",
                    "--base",
                    "catalog-api=http://127.0.0.1:1",
                ]
            )
            self.assertEqual(code, 1)

    def test_missing_map_key_is_a_failure_not_a_crash(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "system.json"
            path.write_text('{"system": "Sample"}', encoding="utf-8")
            code = system_e2e.main(["--map", str(path), "--check"])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
