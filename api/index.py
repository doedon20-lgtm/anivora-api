import os
import json
import base64
import hashlib
import hmac
import urllib.request
import urllib.error

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="AniVora API")


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ENVIRONMENT VARIABLES
# ---------------------------------------------------------

def get_openai_key():
    return os.getenv("OPENAI_API_KEY")


def get_anivora_secret():
    return os.getenv("ANIVORA_API_SECRET")


# ---------------------------------------------------------
# API KEY CREATION
# ---------------------------------------------------------

def create_api_key(name: str, email: str):
    secret = get_anivora_secret()

    if not secret:
        raise RuntimeError("ANIVORA_API_SECRET is not configured")

    payload = {
        "name": name,
        "email": email
    }

    payload_json = json.dumps(
        payload,
        separators=(",", ":")
    ).encode("utf-8")

    payload_encoded = base64.urlsafe_b64encode(
        payload_json
    ).decode("utf-8").rstrip("=")

    signature = hmac.new(
        secret.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return f"av_{payload_encoded}.{signature}"


# ---------------------------------------------------------
# API KEY VERIFICATION
# ---------------------------------------------------------

def verify_api_key(api_key: str):
    secret = get_anivora_secret()

    if not secret:
        return None

    if not api_key:
        return None

    if not api_key.startswith("av_"):
        return None

    token = api_key[3:]

    if "." not in token:
        return None

    payload_encoded, signature = token.rsplit(".", 1)

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        signature,
        expected_signature
    ):
        return None

    try:
        padding = "=" * (-len(payload_encoded) % 4)

        payload_json = base64.urlsafe_b64decode(
            payload_encoded + padding
        )

        payload = json.loads(
            payload_json.decode("utf-8")
        )

        return payload

    except Exception:
        return None


# ---------------------------------------------------------
# OPENAI RESPONSES API
# ---------------------------------------------------------

def extract_output(response_data):
    if "output_text" in response_data:
        return response_data["output_text"]

    output = response_data.get("output", [])

    pieces = []

    for item in output:
        if item.get("type") != "message":
            continue

        content = item.get("content", [])

        for part in content:
            if part.get("type") == "output_text":
                text = part.get("text", "")

                if text:
                    pieces.append(text)

    return "\n".join(pieces).strip()


def call_openai(prompt: str):
    openai_key = get_openai_key()

    if not openai_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured in Vercel"
        )

    url = "https://api.openai.com/v1/responses"

    data = {
        "model": "gpt-5.6-luna",
        "input": prompt
    }

    body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_key}"
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            response_body = response.read().decode(
                "utf-8"
            )

            response_data = json.loads(
                response_body
            )

            output = extract_output(
                response_data
            )

            if not output:
                raise RuntimeError(
                    "OpenAI returned no text output"
                )

            return output

    except urllib.error.HTTPError as error:
        error_body = error.read().decode(
            "utf-8",
            errors="replace"
        )

        try:
            error_json = json.loads(error_body)

            message = (
                error_json
                .get("error", {})
                .get("message")
            )

            if message:
                raise RuntimeError(
                    f"OpenAI API error: {message}"
                )

        except json.JSONDecodeError:
            pass

        raise RuntimeError(
            f"OpenAI API returned HTTP {error.code}"
        )

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Could not connect to OpenAI: {error.reason}"
        )


# ---------------------------------------------------------
# MAIN WEB PAGE
# ---------------------------------------------------------

HTML_PAGE = """
<!DOCTYPE html>

<html>
<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<title>AniVora API</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #0b1020;
    color: white;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 800px;
    margin: auto;
}

.card {
    background: #151c33;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 14px;
}

h1 {
    margin-top: 0;
}

h2 {
    margin-top: 0;
}

input,
textarea,
button {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    margin-top: 10px;
    border-radius: 8px;
    border: none;
    font-size: 16px;
}

input,
textarea {
    background: #222b49;
    color: white;
}

textarea {
    min-height: 120px;
    resize: vertical;
}

button {
    background: #6c5ce7;
    color: white;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

pre {
    background: #080c18;
    padding: 15px;
    border-radius: 8px;
    white-space: pre-wrap;
    word-break: break-word;
}

.success {
    color: #55efc4;
}

.error {
    color: #ff7675;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>🚀 AniVora API</h1>

<p>
Build with AniVora's AI API.
</p>

</div>


<div class="card">

<h2>Developer Registration</h2>

<input
    id="name"
    placeholder="Your name"
/>

<input
    id="email"
    type="email"
    placeholder="Your email"
/>

<button onclick="registerDeveloper()">
Create AniVora API Key
</button>

<pre id="registerResult"></pre>

</div>


<div class="card">

<h2>🤖 AI Generation Test</h2>

<input
    id="apiKey"
    placeholder="AniVora API key (av_...)"
/>

<textarea
    id="prompt"
    placeholder="Write your prompt here..."
></textarea>

<button onclick="generateAI()">
✨ Generate with AniVora AI
</button>

<pre id="generateResult"></pre>

</div>


<div class="card">

<h2>API Status</h2>

<pre id="status">Checking...</pre>

</div>

</div>


<script>

async function registerDeveloper() {

    const name =
        document.getElementById("name").value.trim();

    const email =
        document.getElementById("email").value.trim();

    const result =
        document.getElementById("registerResult");

    if (!name || !email) {

        result.textContent =
            "Please enter your name and email.";

        return;
    }

    result.textContent =
        "Creating API key...";

    try {

        const response = await fetch("/", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                name: name,
                email: email
            })

        });

        const data =
            await response.json();

        result.textContent =
            JSON.stringify(data, null, 2);

        if (data.api_key) {

            document.getElementById(
                "apiKey"
            ).value = data.api_key;

        }

    } catch (error) {

        result.textContent =
            "Error: " + error.message;

    }

}


async function generateAI() {

    const apiKey =
        document.getElementById("apiKey").value.trim();

    const prompt =
        document.getElementById("prompt").value.trim();

    const result =
        document.getElementById("generateResult");

    if (!apiKey) {

        result.textContent =
            "Please enter your AniVora API key.";

        return;
    }

    if (!prompt) {

        result.textContent =
            "Please enter a prompt.";

        return;
    }

    result.textContent =
        "Generating with AI...";

    try {

        const response = await fetch(
            "/v1/generate",
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Authorization":
                        "Bearer " + apiKey
                },

                body: JSON.stringify({
                    prompt: prompt
                })

            }
        );

        const data =
            await response.json();

        result.textContent =
            JSON.stringify(data, null, 2);

    } catch (error) {

        result.textContent =
            "Error: " + error.message;

    }

}


async function checkStatus() {

    try {

        const response =
            await fetch("/v1/status");

        const data =
            await response.json();

        document.getElementById(
            "status"
        ).textContent =
            JSON.stringify(data, null, 2);

    } catch (error) {

        document.getElementById(
            "status"
        ).textContent =
            "Status check failed: " +
            error.message;

    }

}

checkStatus();

</script>

</body>

</html>
"""


# ---------------------------------------------------------
# ROOT PAGE
# ---------------------------------------------------------

@app.get("/")
async def home():
    return HTMLResponse(HTML_PAGE)


# ---------------------------------------------------------
# DEVELOPER REGISTRATION
# ---------------------------------------------------------

@app.post("/")
async def register(request: Request):

    try:
        data = await request.json()

    except Exception:
        return {
            "success": False,
            "error": "Invalid JSON request"
        }

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip()

    if not name:
        return {
            "success": False,
            "error": "Name is required"
        }

    if not email:
        return {
            "success": False,
            "error": "Email is required"
        }

    try:

        api_key = create_api_key(
            name,
            email
        )

        return {
            "success": True,
            "developer": {
                "name": name,
                "email": email
            },
            "api_key": api_key,
            "message": "AniVora API key created successfully"
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


# ---------------------------------------------------------
# API STATUS
# ---------------------------------------------------------

@app.get("/v1/status")
async def status():

    return {
        "success": True,
        "service": "AniVora API",
        "status": "online",
        "ai": "OpenAI",
        "model": "gpt-5.6-luna"
    }


# ---------------------------------------------------------
# AVAILABLE MODELS
# ---------------------------------------------------------

@app.get("/v1/models")
async def models():

    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "provider": "openai",
                "model": "gpt-5.6-luna"
            }
        ]
    }


# ---------------------------------------------------------
# REAL AI GENERATION
# ---------------------------------------------------------

@app.post("/v1/generate")
async def generate(request: Request):

    authorization = request.headers.get(
        "Authorization",
        ""
    )

    if not authorization.startswith(
        "Bearer "
    ):
        return {
            "success": False,
            "error": "Missing AniVora API key"
        }

    api_key = authorization[
        len("Bearer "):
    ].strip()

    developer = verify_api_key(
        api_key
    )

    if not developer:
        return {
            "success": False,
            "error": "Invalid AniVora API key"
        }

    try:
        data = await request.json()

    except Exception:
        return {
            "success": False,
            "error": "Invalid JSON request"
        }

    prompt = str(
        data.get("prompt", "")
    ).strip()

    if not prompt:
        return {
            "success": False,
            "error": "Prompt is required"
        }

    try:

        output = call_openai(
            prompt
        )

        return {
            "success": True,
            "model": "anivora-text",
            "provider": "openai",
            "output": output,
            "prompt": prompt,
            "developer": {
                "name": developer.get("name"),
                "email": developer.get("email")
            }
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
}
