from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "dist"


class SpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path.startswith("/assets/") or self.path.startswith("/sample_data/") or self.path in {"/index.html", "/"}:
            return super().do_GET()

        requested = (ROOT / self.path.lstrip("/")).resolve()
        if requested.exists() and requested.is_file():
            return super().do_GET()

        self.path = "/index.html"
        return super().do_GET()


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 5175), SpaHandler)
    print("Serving frontend on http://127.0.0.1:5175")
    server.serve_forever()


if __name__ == "__main__":
    main()
