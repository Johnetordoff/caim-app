from __future__ import annotations

import http.server
import os
import socketserver
from pathlib import Path

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "10000"))
ROOT = Path(__file__).resolve().parent


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main() -> None:
    def handler(*args, **kwargs):
        return http.server.SimpleHTTPRequestHandler(*args, directory=str(ROOT), **kwargs)

    print(f"Jet2D / Chemimals playtest host listening on {HOST}:{PORT}")
    with ReusableTCPServer((HOST, PORT), handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
