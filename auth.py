import secrets
from database import create_developer, create_api_key


def register_developer(name, email):

    if not name or not email:
        return {
            "success": False,
            "error": "Name and email are required."
        }

    try:
        developer_id = create_developer(
            name,
            email
        )

    except Exception:
        return {
            "success": False,
            "error": "An account with this email may already exist."
        }

    api_key = "av_" + secrets.token_urlsafe(32)

    create_api_key(
        developer_id,
        api_key,
        "Default API Key"
    )

    return {
        "success": True,
        "developer": {
            "id": developer_id,
            "name": name,
            "email": email
        },
        "api_key": api_key
    }


if __name__ == "__main__":

    print("AniVora Developer Registration")
    print("--------------------------------")

    name = input("Name: ").strip()
    email = input("Email: ").strip()

    result = register_developer(
        name,
        email
    )

    print()

    print(result)
