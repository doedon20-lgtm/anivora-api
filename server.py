from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from database import create_tables
from routes import handle_register, handle_health, handle_models


HOST = "0.0.0.0"
PORT = 8000


class AniVoraAPI(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):

        response = json.dumps(data).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
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

        self.wfile.write(response)

    def do_OPTIONS(self):

        self.send_json({
            "success": True
        })

    def do_GET(self):

        if self.path == "/":

            self.send_json({
                "name": "AniVora API",
                "status": "online",
                "version": "v1"
            })

            return

        if self.path == "/v1/status":

            self.send_json(
                handle_health()
            )

            return

        if self.path == "/v1/models":

            self.send_json(
                handle_models()
            )

            return

        self.send_json({
            "success": False,
            "error": {
                "code": "not_found",
                "message": "Endpoint not found."
            }
        }, 404)

    def do_POST(self):

        if self.path == "/v1/register":

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(
                content_length
            ).decode("utf-8")

            result = handle_register(
                body
            )

            if result.get("success"):

                self.send_json(
                    result,
                    201
                )

            else:

                self.send_json(
                    result,
                    400
                )

            return

        self.send_json({
            "success": False,
            "error": {
                "code": "not_found",
                "message": "Endpoint not found."
            }
        }, 404)


def start_server():

    # Create the database tables
    # automatically when the server starts.
    create_tables()

    server = HTTPServer(
        (HOST, PORT),
        AniVoraAPI
    )

    print("================================")
    print("       AniVora API")
    print("================================")
    print("")
    print("Server: http://localhost:8000")
    print("")
    print("Endpoints:")
    print("GET  /")
    print("GET  /v1/status")
    print("GET  /v1/models")
    print("POST /v1/register")
    print("")
    print("Database initialized.")
    print("AniVora API is running.")
    print("")

    server.serve_forever()


if __name__ == "__main__":
    start_server()
