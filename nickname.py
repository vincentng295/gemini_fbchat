import re
from unidecode import unidecode

def generate(fullname, existing_usernames):
    if not fullname:
        return None

    # Normalize: Unicode → ASCII, lowercase
    normalized = unidecode(fullname).lower()
    
    # Keep only a-zA-Z0-9
    base = re.sub(r'[^a-z0-9]', '', normalized)
    
    # Return None if result is empty
    if not base:
        return None

    candidate = base
    counter = 1
    while candidate in existing_usernames:
        candidate = f"{base}.{counter}"
        counter += 1
    
    return candidate
