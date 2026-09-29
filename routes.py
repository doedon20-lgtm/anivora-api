import json
from auth import register_developer


def handle_register(body):

    try:
        data = json.loads(body)

    except json.JSONDecodeError:

        return {
            "success": False,
            "error": "Invalid JSON."
        }

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()

    if not name or not email:

        return {
            "success": False,
            "error": "Name and email are required."
        }

    return register_developer(
        name,
        email
    )


def handle_health():

    return {
        "success": True,
        "service": "AniVora API",
        "status": "operational",
        "version": "v1"
    }


def handle_models():

    return {
        "success": True,
        "models": [
            {
                "id": "anivora-ai",
                "name": "AniVora AI",
                "type": "text",
                "status": "development"
            }
        ]
    }
