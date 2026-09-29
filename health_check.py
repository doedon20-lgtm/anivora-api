import json
import urllib.request
import urllib.error
import sys


API_URL = "http://127.0.0.1:8000"


def check_endpoint(path):
    url = API_URL + path

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json"
        },
        method="GET"
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=10
        ) as response:

            raw = response.read().decode(
                "utf-8",
                errors="replace"
            )

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print(
                    f"FAIL  {path}: invalid JSON"
                )
                return False

            print(
                f"PASS  {path}: HTTP {response.status}"
            )

            return data

    except urllib.error.URLError as error:
        print(
            f"FAIL  {path}: API unavailable"
        )
        print(
            f"      {error}"
        )
        return False

    except Exception as error:
        print(
            f"FAIL  {path}: {error}"
        )
        return False


def main():
    print("")
    print("========================================")
    print("       AniVora API Health Check")
    print("========================================")
    print("")

    status = check_endpoint(
        "/v1/status"
    )

    if status is False:
        print("")
        print("AniVora API is not reachable.")
        print("")
        sys.exit(1)

    models = check_endpoint(
        "/v1/models"
    )

    if models is False:
        print("")
        print("Model endpoint failed.")
        print("")
        sys.exit(1)

    print("")
    print("AniVora API health check passed.")
    print("")


if __name__ == "__main__":
    main()
