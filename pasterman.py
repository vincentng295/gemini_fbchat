import requests

def post_to_0x0(text):
    headers = {
        "User-Agent": "curl/7.88.1"  # Mimics a typical curl request
    }
    try:
        response = requests.post(
            "https://0x0.st",
            files={'file': ('text.txt', text)},
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            return response.text.strip()
        else:
            raise Exception(f"Failed to post: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout:
        raise Exception("Request timed out.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")