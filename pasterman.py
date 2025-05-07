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

def post_to_dpaste(content, syntax='text', expiry_days=1):
    url = 'https://dpaste.org/api/'
    data = {
        'content': content,
        'syntax': syntax,
        'expiry_days': expiry_days
    }
    try:
        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        else:
            raise Exception(f"Failed to post: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout:
        raise Exception("Request to dpaste timed out.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request to dpaste failed: {e}")

def pasterman(text):
    try:
        return post_to_dpaste(text)
    except Exception as e1:
        #print(f"dpaste failed: {e1}")
        try:
            return post_to_0x0(text)
        except Exception as e2:
            #print(f"0x0 failed: {e2}")
            raise Exception("Cannot generate link for text")
