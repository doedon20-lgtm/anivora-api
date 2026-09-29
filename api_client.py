import json
import urllib.request
import urllib.error


class AniVoraAPIError(Exception):
    pass


class AniVoraClient:
    def __init__(self, api_key, base_url="http://127.0.0.1:8000"):
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method, endpoint, data=None):
        url = self.base_url + endpoint

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        body = None

        if data is not None:
            body = json.dumps(data).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method=method
        )

        try:
            with urllib.request.urlopen(request) as response:
                raw = response.read().decode("utf-8")

        except urllib.error.HTTPError as error:
            raw = error.read().decode("utf-8")

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"error": raw}

            raise AniVoraAPIError(
                data.get("error", "AniVora API request failed")
            )

        except urllib.error.URLError as error:
            raise AniVoraAPIError(
                f"Unable to connect to AniVora API: {error.reason}"
            )

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            raise AniVoraAPIError(
                "AniVora API returned invalid JSON"
            )

        return result

    def status(self):
        return self._request(
            "GET",
            "/v1/status"
        )

    def models(self):
        return self._request(
            "GET",
            "/v1/models"
        )

    def generate(self, prompt, model="anivora-text"):
        if not prompt or not str(prompt).strip():
            raise ValueError("Prompt is required")

        return self._request(
            "POST",
            "/v1/generate",
            {
                "model": model,
                "prompt": prompt
            }
        )


if __name__ == "__main__":
    print("AniVora API Python client")
    print("Import AniVoraClient to use the API.")
