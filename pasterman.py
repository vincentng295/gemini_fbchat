import requests

def post_to_pasters(text):
    r = requests.post("https://paste.rs", files={'file': ('text.txt', text)}, timeout=5)
    if r.status_code == 200 or r.status_code == 201:
        return r.text.strip()
    else:
        raise Exception(f"paste.rs failed: {r.status_code}")

def pasterman(text):
    return post_to_pasters(text)
