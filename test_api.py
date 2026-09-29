import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def request(method, path, data=None, api_key=None):
    url = BASE_URL + path

    headers = {
        "Content-Type": "application/json"
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read().decode("utf-8")

            return response.status, json.loads(raw)

    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"raw": raw}

        return error.code, data


def check(name, condition):
    if condition:
        print(f"PASS  {name}")
        return True

    print(f"FAIL  {name}")
    return False


def main():

    print("")
    print("================================")
    print("     AniVora API Test Suite")
    print("================================")
    print("")

    # 1. Health
    status, data = request(
        "GET",
        "/v1/status"
    )

    check(
        "API health",
        status == 200
        and data.get("success") is True
        and data.get("status") == "online"
    )

    # 2. Models
    status, data = request(
        "GET",
        "/v1/models"
    )

    check(
        "Models endpoint",
        status == 200
        and isinstance(data.get("models"), list)
    )

    # 3. Registration
    status, data = request(
        "POST",
        "/v1/register",
        {
            "name": "AniVora Test Developer",
            "email": "test@example.com"
        }
    )

    api_key = data.get("api_key")

    check(
        "Developer registration",
        status == 201
        and data.get("success") is True
        and isinstance(api_key, str)
        and api_key.startswith("av_")
    )

    if not api_key:
        print("")
        print("Cannot continue without API key.")
        return

    # 4. Authenticated generation
    status, data = request(
        "POST",
        "/v1/generate",
        {
            "model": "anivora-text",
            "prompt": "Hello from AniVora API"
        },
        api_key
    )

    check(
        "Authenticated generation",
        status == 200
        and data.get("success") is True
        and data.get("model") == "anivora-text"
    )

    # 5. Invalid API key
    status, data = request(
        "POST",
        "/v1/generate",
        {
            "prompt": "This should fail"
        },
        "av_invalid_key"
    )

    check(
        "Invalid API key rejected",
        status == 401
        and "error" in data
    )

    # 6. Missing API key
    status, data = request(
        "POST",
        "/v1/generate",
        {
            "prompt": "This should fail"
        }
    )

    check(
        "Missing API key rejected",
        status == 401
        and "error" in data
    )

    # 7. Missing prompt
    status, data = request(
        "POST",
        "/v1/generate",
        {},
        api_key
    )

    check(
        "Missing prompt rejected",
        status == 400
        and "error" in data
    )

    # 8. Unknown model
    status, data = request(
        "POST",
        "/v1/generate",
        {
            "model": "does-not-exist",
            "prompt": "Test"
        },
        api_key
    )

    check(
        "Unknown model rejected",
        status == 400
        and "error" in data
    )

    # 9. Malformed JSON
    url = BASE_URL + "/v1/generate"

    req = urllib.request.Request(
        url,
        data=b'{"prompt":',
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            malformed_status = response.status
            malformed_data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:
        malformed_status = error.code
        malformed_data = json.loads(
            error.read().decode("utf-8")
        )

    check(
        "Malformed JSON rejected",
        malformed_status == 400
        and "error" in malformed_data
    )

    # 10. 404 handling
    status, data = request(
        "GET",
        "/does-not-exist"
    )

    check(
        "Unknown endpoint rejected",
        status == 404
        and "error" in data
    )

    print("")
    print("================================")
    print("        Tests completed")
    print("================================")
    print("")


if __name__ == "__main__":
    main()
