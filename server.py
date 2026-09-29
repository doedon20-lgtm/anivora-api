from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from database import create_tables
from routes import (
    handle_register,
    handle_health,
    handle_models,
    handle_generate,
)


class AniVoraHandler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        payload = json.dumps(data).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(payload))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.end_headers()

        self.wfile.write(payload)

    def read_body(self):
        try:
            length = int(
                self.headers.get("Content-Length", "0")
            )
        except ValueError:
            length = 0

        if length <= 0:
            return ""

        return self.rfile.read(length).decode(
            "utf-8",
            errors="replace"
        )

    def do_OPTIONS(self):
        self.send_response(204)

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.end_headers()

    def do_GET(self):

        if self.path == "/":
            self.send_json(
                200,
                {
                    "success": True,
                    "service": "AniVora API",
                    "version": "v1",
                    "message": "AniVora API is running"
                }
            )
            return

        if self.path == "/v1/status":
            result = handle_health()

            self.send_json(
                result["status"],
                result["body"]
            )
            return

        if self.path == "/v1/models":
            result = handle_models()

            self.send_json(
                result["status"],
                result["body"]
            )
            return

        self.send_json(
            404,
            {
                "error": "Endpoint not found"
            }
        )

    def do_POST(self):

        body = self.read_body()

        if self.path == "/v1/register":
            result = handle_register(body)

            self.send_json(
                result["status"],
                result["body"]
            )
            return

        if self.path == "/v1/generate":
            result = handle_generate(
                body,
                self.headers
            )

            self.send_json(
                result["status"],
                result["body"]
            )
            return

        self.send_json(
            404,
            {
                "error": "Endpoint not found"
            }
        )

    def log_message(self, format, *args):
        print(
            "[AniVora API]",
            format % args
        )


def start_server():
    create_tables()

    server = HTTPServer(
        ("0.0.0.0", 8000),
        AniVoraHandler
    )

    print("")
    print("================================")
    print("       AniVora API v1")
    print("================================")
    print("")
    print("Server: http://0.0.0.0:8000")
    print("")
    print("GET  /")
    print("GET  /v1/status")
    print("GET  /v1/models")
    print("POST /v1/register")
    print("POST /v1/generate")
    print("")
    print("API is ready.")
    print("")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping AniVora API...")
    finally:
        server.server_close()


if __name__ == "__main__":
    start_server()
