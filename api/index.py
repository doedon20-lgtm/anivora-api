from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import secrets
import re

app = FastAPI(
    title="AniVora API",
    version="1.0.0"
)

developers = {}


PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AniVora API</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 650px;
            margin: 40px auto;
            padding: 20px;
            background: #0b1020;
            color: white;
        }

        input, textarea, button {
            width: 100%;
            padding: 14px;
            margin-top: 12px;
            box-sizing: border-box;
            border-radius: 8px;
            border: none;
        }

        textarea {
            min-height: 120px;
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

        hr {
            margin: 30px 0;
            border: 0;
            border-top: 1px solid #333;
        }
    </style>
</head>

<body>

<h1>AniVora API</h1>

<h2>Developer Registration</h2>

<input id="name" placeholder="Your name">

<input id="email" type="email" placeholder="Your email">

<button onclick="register()">
    Create API Key
</button>

<pre id="registerResult">Enter your details above.</pre>

<hr>

<h2>AI Generation Test</h2>

<input id="apiKey" placeholder="Paste your av_ API key">

<textarea
    id="prompt"
    placeholder="Enter a prompt..."
></textarea>

<button onclick="generate()">
    Generate
</button>

<pre id="generateResult">Waiting for a request.</pre>

<script>

async function register() {

    const result =
        document.getElementById("registerResult");

    result.textContent = "Creating API key...";

    try {

        const response = await fetch("/", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                name:
                    document.getElementById("name").value,

                email:
                    document.getElementById("email").value
            })
        });

        const data = await response.json();

        result.textContent =
            JSON.stringify(data, null, 2);

        if (data.api_key) {
            document.getElementById("apiKey").value =
                data.api_key;
        }

    } catch (error) {

        result.textContent =
            JSON.stringify({
                success: false,
                error: error.message
            }, null, 2);
    }
}


async function generate() {

    const result =
        document.getElementById("generateResult");

    const apiKey =
        document.getElementById("apiKey").value.trim();

    const prompt =
        document.getElementById("prompt").value.trim();

    if (!apiKey) {
        result.textContent = "API key is required.";
        return;
    }

    if (!prompt) {
        result.textContent = "Prompt is required.";
        return;
    }

    result.textContent = "Generating...";

    try {

        const response = await fetch(
            "/v1/generate",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + apiKey
                },

                body: JSON.stringify({
                    model: "anivora-text",
                    prompt: prompt
                })
            }
        );

        const data = await response.json();

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


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE


@app.post("/")
async def register_from_root(request: Request):

    try:

        data = await request.json()

        name = str(
            data.get("name", "")
        ).strip()

        email = str(
            data.get("email", "")
        ).strip().lower()

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

        api_key = (
            "av_" +
            secrets.token_urlsafe(32)
        )

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


@app.post("/v1/generate")
async def generate(request: Request):

    authorization = request.headers.get(
        "Authorization",
        ""
    )

    if not authorization.startswith("Bearer "):

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "API key is required"
            }
        )

    api_key = authorization[7:].strip()

    developer = None

    for account in developers.values():

        if account["api_key"] == api_key:
            developer = account
            break

    if developer is None:

        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": "Invalid API key"
            }
        )

    try:

        data = await request.json()

        prompt = str(
            data.get("prompt", "")
        ).strip()

        model = str(
            data.get("model", "anivora-text")
        ).strip()

        if not prompt:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Prompt is required"
                }
            )

        if model != "anivora-text":

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Unknown model"
                }
            )

        return {
            "success": True,
            "model": "anivora-text",
            "output": "AniVora AI generation endpoint is connected. Real model inference will be connected next.",
            "prompt": prompt
        }

    except Exception as error:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(error)
            }
        )

Push it to GitHub and wait for Vercel to deploy.

Then:

1. Open your AniVora API page.
2. Enter your name/email.
3. Tap Create API Key.
4. Put the generated "av_..." key into the API-key box.
5. Enter a prompt such as:
   "Write a short welcome message for a Nigerian restaurant."
6. Tap Generate.

You should get a successful response from "/v1/generate".

Important: this step verifies the authentication pipeline. The returned text is still a test response; after this works, the next step is connecting an actual AI inference provider.
