import json
import secrets
from database import (
    create_developer,
    create_api_key,
    get_api_key,
    increment_requests,
    log_request,
)


def json_response(data):
    return data


def handle_register(body):
    try:
        data = json.loads(body or "{}")
    except json.JSONDecodeError:
        return {
            "status": 400,
            "body": {
                "error": "Malformed JSON"
            }
        }

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()

    if not name:
        return {
            "status": 400,
            "body": {
                "error": "Name is required"
            }
        }

    if not email or "@" not in email:
        return {
            "status": 400,
            "body": {
                "error": "A valid email is required"
            }
        }

    try:
        developer = create_developer(name, email)

        api_key = "av_" + secrets.token_urlsafe(32)

        key_record = create_api_key(
            developer["id"],
            api_key,
            "Default API Key"
        )

        return {
            "status": 201,
            "body": {
                "success": True,
                "developer": {
                    "id": developer["id"],
                    "name": developer["name"],
                    "email": developer["email"]
                },
                "api_key": key_record["key"]
            }
        }

    except Exception as error:
        return {
            "status": 500,
            "body": {
                "error": str(error)
            }
        }


def handle_health():
    return {
        "status": 200,
        "body": {
            "success": True,
            "status": "online",
            "service": "AniVora API",
            "version": "v1"
        }
    }


def handle_models():
    return {
        "status": 200,
        "body": {
            "success": True,
            "models": [
                {
                    "id": "anivora-text",
                    "type": "text-generation",
                    "status": "available"
                }
            ]
        }
    }


def authenticate_api_key(headers):
    authorization = headers.get("Authorization", "")

    if not authorization.startswith("Bearer "):
        return None

    api_key = authorization[7:].strip()

    if not api_key:
        return None

    return get_api_key(api_key)


def handle_generate(body, headers):
    api_key = authenticate_api_key(headers)

    if not api_key:
        return {
            "status": 401,
            "body": {
                "error": "Invalid or missing API key"
            }
        }

    try:
        data = json.loads(body or "{}")
    except json.JSONDecodeError:
        return {
            "status": 400,
            "body": {
                "error": "Malformed JSON"
            }
        }

    prompt = str(data.get("prompt", "")).strip()

    if not prompt:
        return {
            "status": 400,
            "body": {
                "error": "prompt is required"
            }
        }

    model = str(
        data.get("model", "anivora-text")
    ).strip()

    if model != "anivora-text":
        return {
            "status": 400,
            "body": {
                "error": f"Unknown model: {model}"
            }
        }

    try:
        increment_requests(api_key["id"])

        log_request(
            developer_id=api_key["developer_id"],
            api_key_id=api_key["id"],
            endpoint="/v1/generate",
            model=model,
            status="success"
        )

        return {
            "status": 200,
            "body": {
                "success": True,
                "model": model,
                "output": {
                    "text": (
                        "AniVora API received your request successfully. "
                        f"Prompt: {prompt}"
                    )
                }
            }
        }

    except Exception as error:
        log_request(
            developer_id=api_key["developer_id"],
            api_key_id=api_key["id"],
            endpoint="/v1/generate",
            model=model,
            status="error"
        )

        return {
            "status": 500,
            "body": {
                "error": str(error)
            }
  }
