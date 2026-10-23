"""Loopback-only web UI. Mutations require a same-origin session token."""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
from urllib.parse import urlsplit

from .engine import Bench
from .store import Store

STATIC = Path(__file__).parent / "static"


def create_server(port=8765, data_dir=".forgebench-lab", bench=None):
    engine = bench or Bench(Store(data_dir))
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def trusted_host(self):
            return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

        def send(self, body, status=200, content_type="application/json", download=False):
            raw = json.dumps(body).encode() if content_type == "application/json" else body
            self.send_response(status)
            self.send_header("Content-Type", content_type + "; charset=utf-8" if not content_type.startswith("image/") else content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if download:
                self.send_header("Content-Disposition", 'attachment; filename="forgebench-run.json"')
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if not self.trusted_host():
                return self.send({"error": "Only local access is allowed."}, 403)
            path = urlsplit(self.path).path
            if path == "/api/bootstrap":
                return self.send({**engine.bootstrap(), "token": token})
            if path == "/api/runs":
                return self.send(engine.runs())
            if path.startswith("/api/runs/"):
                parts = path.split("/")
                run = engine.store.get("run", parts[3])
                return self.send(run, download=path.endswith("/export")) if run else self.send({"error": "Run not found."}, 404)
            if path.startswith("/api/"):
                return self.send({"error": "Not found."}, 404)
            target = (STATIC / ("index.html" if path == "/" else path.lstrip("/"))).resolve()
            if not target.is_relative_to(STATIC.resolve()) or not target.is_file():
                return self.send({"error": "Not found."}, 404)
            self.send(target.read_bytes(), content_type=mimetypes.guess_type(target.name)[0] or "application/octet-stream")

        def do_POST(self):
            origin = self.headers.get("Origin")
            allowed_origins = {f"http://localhost:{self.server.server_port}", f"http://127.0.0.1:{self.server.server_port}"}
            if (not self.trusted_host() or origin not in allowed_origins
                    or not secrets.compare_digest(self.headers.get("X-ForgeBench-Token", ""), token)):
                return self.send({"error": "Local session required. Reload ForgeBench and retry."}, 403)
            try:
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("Send a JSON request.")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536:
                    raise ValueError("Request body must be between 1 and 65,536 bytes.")
                self.connection.settimeout(10)
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Request must be a JSON object.")
                path = urlsplit(self.path).path
                if path == "/api/runs":
                    return self.send(engine.start(data), 201)
                if path == "/api/settings":
                    return self.send(engine.save_settings(data))
                if path == "/api/cases":
                    return self.send(engine.save_case(data), 201)
                if path == "/api/cases/delete":
                    engine.delete_case(data.get("id"))
                    return self.send({"deleted": True})
                if path.endswith("/cancel") and path.startswith("/api/runs/"):
                    return self.send(engine.cancel(path.split("/")[3]))
                return self.send({"error": "Not found."}, 404)
            except (ValueError, TypeError, UnicodeDecodeError) as exc:
                return self.send({"error": str(exc)}, 400)
            except (TimeoutError, OSError):
                return self.send({"error": "Local request or storage unavailable. Check available disk space and retry."}, 503)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.bench = engine
    return server


def serve(port=8765, data_dir=".forgebench-lab"):
    server = create_server(port, data_dir)
    print(f"ForgeBench LLM test bench: http://127.0.0.1:{server.server_port}", flush=True)
    print(f"Local run storage: {server.bench.store.directory}", flush=True)
    print("No model calls occur until you start a run. Ctrl-C stops the server.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.bench.close()
    return 0
