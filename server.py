from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import uuid
from datetime import datetime


HOST = "0.0.0.0"
PORT = 8000


class AniVoraAPI(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        response = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

        self.wfile.write(response)

    def do_OPTIONS(self):
        self.send_json({"success": True})

    def do_GET(self):

        if self.path == "/":
            self.send_json({
                "name": "AniVora API",
                "status": "online",
                "version": "v1",
                "message": "Welcome to AniVora API"
            })
            return

        if self.path == "/v1/status":
            self.send_json({
                "success": True,
                "service": "AniVora API",
                "status": "operational",
                "version": "v1"
            })
            return

        if self.path == "/v1/models":
            self.send_json({
                "success": True,
                "models": [
                    {
                        "id": "anivora-ai",
                        "type": "text",
                        "status": "development"
                    }
                ]
            })
            return

        self.send_json({
            "success": False,
            "error": "Endpoint not found"
        }, 404)

    def do_POST(self):

        if self.path != "/v1/generate":
            self.send_json({
                "success": False,
                "error": "Endpoint not found"
            }, 404)
            return

        content_length = int(
            self.headers.get("Content-Length", 0)
        )

        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({
                "success": False,
                "error": "Invalid JSON"
            }, 400)
            return

        prompt = data.get("prompt")

        if not prompt:
            self.send_json({
                "success": False,
                "error": "A prompt is required"
            }, 400)
            return

        request_id = "req_" + uuid.uuid4().hex[:12]

        self.send_json({
            "success": True,
            "request_id": request_id,
            "model": data.get("model", "anivora-ai"),
            "prompt": prompt,
            "result": {
                "message": "AniVora AI received your request.",
                "status": "queued"
            },
            "created_at": datetime.utcnow().isoformat() + "Z"
        })


if __name__ == "__main__":

    print("================================")
    print("       AniVora API Server")
    print("================================")
    print(f"Server running on port {PORT}")
    print("API version: v1")
    print("")
    print("Endpoints:")
    print("GET  /")
    print("GET  /v1/status")
    print("GET  /v1/models")
    print("POST /v1/generate")
    print("")

    server = HTTPServer(
        (HOST, PORT),
        AniVoraAPI
    )

    server.serve_forever()
