import requests


ENGINE_URL = "http://127.0.0.1:8000"


def main():
    print("Testing AniVora Engine...")

    health = requests.get(
        f"{ENGINE_URL}/health",
        timeout=30
    )

    print("\nHEALTH:")
    print(health.json())

    response = requests.post(
        f"{ENGINE_URL}/generate",
        json={
            "prompt": "Write a short welcome message for AniVora.",
            "max_new_tokens": 50,
            "temperature": 0.7
        },
        timeout=300
    )

    print("\nGENERATE:")
    print(response.json())


if __name__ == "__main__":
    main()
