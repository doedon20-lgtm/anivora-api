import json
import time
import urllib.request
import urllib.error
import uuid


BASE_URL = "http://127.0.0.1:8000"


def request(
    method,
    path,
    data=None,
    api_key=None
):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    if api_key:
        headers["Authorization"] = (
            f"Bearer {api_key}"
        )

    body = None

    if data is not None:
        body = json.dumps(data).encode(
            "utf-8"
        )

    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=180
        ) as response:

            raw = response.read().decode(
                "utf-8",
                errors="replace"
            )

            return (
                response.status,
                json.loads(raw)
            )

    except urllib.error.HTTPError as error:

        raw = error.read().decode(
            "utf-8",
            errors="replace"
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "error": raw
            }

        return error.code, data


def main():

    print("")
    print("========================================")
    print("       AniVora Full System Test")
    print("========================================")
    print("")

    # 1. API status
    print("[1/4] Checking API...")

    status, data = request(
        "GET",
        "/v1/status"
    )

    if status != 200:
        print("FAILED:", data)
        return

    print("PASS")

    # 2. Register developer
    print("")
    print("[2/4] Creating test developer...")

    unique_email = (
        "test-" +
        uuid.uuid4().hex +
        "@anivora.local"
    )

    status, data = request(
        "POST",
        "/v1/register",
        {
            "name": "AniVora Test",
            "email": unique_email
        }
    )

    if status != 201:
        print("FAILED:", data)
        return

    api_key = data.get("api_key")

    if not api_key:
        print("FAILED: No API key returned.")
        return

    print("PASS")
    print("API key received.")

    # 3. Models
    print("")
    print("[3/4] Checking models...")

    status, data = request(
        "GET",
        "/v1/models"
    )

    if status != 200:
        print("FAILED:", data)
        return

    print("PASS")

    # 4. Real generation
    print("")
    print("[4/4] Calling real AI generation...")
    print("")
    print("Waiting for model response...")

    status, data = request(
        "POST",
        "/v1/generate",
        {
            "model": "anivora-text",
            "prompt": (
                "Explain what AniVora API is "
                "in two short sentences."
            )
        },
        api_key
    )

    if status != 200:
        print("")
        print("GENERATION FAILED")
        print(data)
        return

    output = (
        data
        .get("output", {})
        .get("text")
    )

    if not output:
        print("")
        print("FAILED: AI returned no text.")
        print(data)
        return

    print("")
    print("========================================")
    print("          REAL AI RESPONSE")
    print("========================================")
    print("")
    print(output)
    print("")
    print("========================================")
    print("       FULL SYSTEM TEST PASSED")
    print("========================================")
    print("")


if __name__ == "__main__":
    main()
