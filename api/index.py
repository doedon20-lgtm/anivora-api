from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import secrets
import re

app = FastAPI(
    title="AniVora API",
    version="1.0.0"
)

developers = {}


@app.get("/", response_class=HTMLResponse)
def root():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AniVora API</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
            background: #0b1020;
            color: white;
        }

        input,
        button {
            width: 100%;
            padding: 14px;
            margin-top: 10px;
            box-sizing: border-box;
            border-radius: 8px;
            border: none;
        }

        button {
            background: #6c5ce7;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        pre {
            white-space: pre-wrap;
            background: #151b30;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
    </style>
</head>

<body>

<h1>AniVora API</h1>

<p>Developer Registration</p>

<input id="name" placeholder="Your name">

<input id="email" type="email" placeholder="Your email">

<button onclick="register()">Create API Key</button>

<pre id="result">Enter your details above.</pre>

<script>
async function register() {

    const result = document.getElementById("result");

    result.textContent = "Creating API key...";

    try {

        const response = await fetch("/api/v1/register", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                name: document.getElementById("name").value,
                email: document.getElementById("email").value
            })
        });

        const text = await response.text();

        let data;

        try {
            data = JSON.parse(text);
        } catch {
            data = {
                success: false,
                error: text
            };
        }

        result.textContent =
            JSON.stringify(data, null, 2);

    } catch (error) {

        result.textContent =
            JSON.stringify({
                success: false,
                error: error.message
            }, null, 2);
    }
}
</script>

</body>
</html>
"""


@app.get("/v1/status")
def status():
    return {
        "success": True,
        "service": "AniVora API",
        "version": "v1",
        "status": "online"
    }


@app.get("/v1/models")
def models():
    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "type": "text-generation",
                "status": "available"
            }
        ]
    }


@app.post("/v1/register")
async def register(request: Request):

    try:
        data = await request.json()

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()

        if not name:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Name is required"
                }
            )

        if not re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            email
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Valid email is required"
                }
            )

        api_key = "av_" + secrets.token_urlsafe(32)

        developers[email] = {
            "name": name,
            "email": email,
            "api_key": api_key
        }

        return {
            "success": True,
            "developer": {
                "name": name,
                "email": email
            },
            "api_key": api_key
        }

    except Exception as error:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(error)
            }
  )
