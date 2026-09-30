import os
import json
import base64
import hashlib
import hmac

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


# =========================================================
# ANIVORA API
# =========================================================

app = FastAPI(
    title="AniVora API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ANIVORA SECRET
# =========================================================

def get_secret():
    return os.getenv("ANIVORA_API_SECRET")


# =========================================================
# CREATE ANIVORA API KEY
# =========================================================

def create_api_key(name, email):

    secret = get_secret()

    if not secret:
        raise RuntimeError(
            "ANIVORA_API_SECRET is not configured"
        )

    payload = {
        "name": name,
        "email": email
    }

    raw = json.dumps(
        payload,
        separators=(",", ":")
    ).encode("utf-8")

    encoded = base64.urlsafe_b64encode(
        raw
    ).decode("utf-8").rstrip("=")

    signature = hmac.new(
        secret.encode("utf-8"),
        encoded.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return "av_" + encoded + "." + signature


# =========================================================
# VERIFY ANIVORA API KEY
# =========================================================

def verify_api_key(api_key):

    secret = get_secret()

    if not secret:
        return None

    if not api_key:
        return None

    if not api_key.startswith("av_"):
        return None

    token = api_key[3:]

    if "." not in token:
        return None

    encoded, signature = token.rsplit(".", 1)

    expected = hmac.new(
        secret.encode("utf-8"),
        encoded.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        signature,
        expected
    ):
        return None

    try:

        padding = "=" * (
            -len(encoded) % 4
        )

        raw = base64.urlsafe_b64decode(
            encoded + padding
        )

        return json.loads(
            raw.decode("utf-8")
        )

    except Exception:
        return None


# =========================================================
# ANIVORA AI ENGINE
# =========================================================

class AniVoraEngine:

    def __init__(self):

        self.name = "AniVora Engine"

        self.version = "0.1.0"

        self.status = "initializing"

        self.model = None

        self.model_name = os.getenv(
            "ANIVORA_MODEL",
            "local"
        )

        self.status = "ready"


    def generate(self, prompt):

        prompt = prompt.strip()

        if not prompt:
            raise ValueError(
                "Prompt cannot be empty"
            )

        # -------------------------------------------------
        # ENGINE PLACEHOLDER
        #
        # This is intentionally NOT OpenAI.
        #
        # The next engine layer will load our local model
        # and perform actual neural-network inference here.
        # -------------------------------------------------

        return (
            "AniVora Engine received your request.\n\n"
            "Prompt:\n"
            + prompt
            + "\n\n"
            "Engine status: ready\n"
            "Model runtime: "
            + self.model_name
            + "\n\n"
            "The neural-network inference layer is the "
            "next component we are building."
        )


engine = AniVoraEngine()


# =========================================================
# WEBSITE
# =========================================================

HTML = """
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>AniVora API</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #0b1020;
    color: white;
    font-family: Arial, sans-serif;
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

input,
textarea,
button {

    width: 100%;
    box-sizing: border-box;

    padding: 13px;

    margin-top: 10px;

    border: none;
    border-radius: 8px;

    font-size: 16px;
}

input,
textarea {

    background: #222b49;
    color: white;
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

    background: #080c18;

    padding: 15px;

    border-radius: 8px;

    white-space: pre-wrap;

    word-break: break-word;
}

</style>

</head>


<body>

<div class="container">


<div class="card">

<h1>🚀 AniVora API</h1>

<p>
Independent AI infrastructure by AniVora.
</p>

</div>


<div class="card">

<h2>Create Developer API Key</h2>

<input
    id="name"
    placeholder="Your name"
/>

<input
    id="email"
    placeholder="Your email"
/>

<button onclick="register()">
Create API Key
</button>

<pre id="registerResult"></pre>

</div>


<div class="card">

<h2>🤖 AniVora Engine</h2>

<input
    id="apiKey"
    placeholder="av_..."
/>

<textarea
    id="prompt"
    placeholder="Enter your prompt..."
></textarea>

<button onclick="generate()">
Generate
</button>

<pre id="result"></pre>

</div>


<div class="card">

<h2>Engine Status</h2>

<pre id="status">
Checking...
</pre>

</div>


</div>


<script>


async function register() {

    const name =
        document.getElementById(
            "name"
        ).value.trim();

    const email =
        document.getElementById(
            "email"
        ).value.trim();

    const result =
        document.getElementById(
            "registerResult"
        );

    if (!name || !email) {

        result.textContent =
            "Name and email are required.";

        return;
    }

    result.textContent =
        "Creating API key...";

    try {

        const response =
            await fetch("/", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    name: name,
                    email: email
                })

            });

        const data =
            await response.json();

        result.textContent =
            JSON.stringify(
                data,
                null,
                2
            );

        if (data.api_key) {

            document.getElementById(
                "apiKey"
            ).value =
                data.api_key;

        }

    } catch (error) {

        result.textContent =
            error.message;

    }
}


async function generate() {

    const apiKey =
        document.getElementById(
            "apiKey"
        ).value.trim();

    const prompt =
        document.getElementById(
            "prompt"
        ).value.trim();

    const result =
        document.getElementById(
            "result"
        );

    if (!apiKey) {

        result.textContent =
            "Enter your AniVora API key.";

        return;
    }

    if (!prompt) {

        result.textContent =
            "Enter a prompt.";

        return;
    }

    result.textContent =
        "AniVora Engine is processing...";

    try {

        const response =
            await fetch(
                "/v1/generate",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

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
            JSON.stringify(
                data,
                null,
                2
            );

    } catch (error) {

        result.textContent =
            error.message;

    }
}


async function checkStatus() {

    try {

        const response =
            await fetch(
                "/v1/status"
            );

        const data =
            await response.json();

        document.getElementById(
            "status"
        ).textContent =
            JSON.stringify(
                data,
                null,
                2
            );

    } catch (error) {

        document.getElementById(
            "status"
        ).textContent =
            error.message;

    }
}


checkStatus();

</script>

</body>

</html>
"""


# =========================================================
# HOME
# =========================================================

@app.get("/")
async def home():

    return HTMLResponse(
        HTML
    )


# =========================================================
# CREATE API KEY
# =========================================================

@app.post("/")
async def register(
    request: Request
):

    try:

        data = await request.json()

    except Exception:

        return {
            "success": False,
            "error": "Invalid JSON"
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

            "api_key": api_key

        }

    except Exception as error:

        return {

            "success": False,

            "error": str(error)

        }


# =========================================================
# STATUS
# =========================================================

@app.get("/v1/status")
async def status():

    return {

        "success": True,

        "service": "AniVora API",

        "engine": "AniVora Engine",

        "engine_version": "0.1.0",

        "status": engine.status,

        "model_runtime":
            engine.model_name

    }


# =========================================================
# MODELS
# =========================================================

@app.get("/v1/models")
async def models():

    return {

        "success": True,

        "models": [

            {
                "id": "anivora-engine",
                "type": "text-generation",
                "provider": "AniVora"
            }

        ]

    }


# =========================================================
# GENERATE
# =========================================================

@app.post("/v1/generate")
async def generate(
    request: Request
):

    authorization =
        request.headers.get(
            "Authorization",
            ""
        )

    if not authorization.startswith(
        "Bearer "
    ):

        return {

            "success": False,

            "error":
                "Missing AniVora API key"

        }

    api_key = authorization[
        7:
    ].strip()

    developer = verify_api_key(
        api_key
    )

    if not developer:

        return {

            "success": False,

            "error":
                "Invalid AniVora API key"

        }

    try:

        data = await request.json()

    except Exception:

        return {

            "success": False,

            "error":
                "Invalid JSON"

        }

    prompt = str(
        data.get("prompt", "")
    ).strip()

    if not prompt:

        return {

            "success": False,

            "error":
                "Prompt is required"

        }

    try:

        output = engine.generate(
            prompt
        )

        return {

            "success": True,

            "engine":
                "AniVora Engine",

            "model":
                engine.model_name,

            "output":
                output,

            "prompt":
                prompt

        }

    except Exception as error:

        return {

            "success": False,

            "error":
                str(error)

        }
