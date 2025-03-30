import pickle
import os
from cryptography.fernet import Fernet
import base64

def pad_string_to_32(input_str: str) -> str:
    # Ensure the string is padded to 32 characters
    return input_str.ljust(32, '\0')

def generate_fernet_key(secret):
    if secret == None:
        secret = ""
    return base64.urlsafe_b64encode(pad_string_to_32(secret).encode("utf-8")[:32])

def encrypt_data(original, key):
    return Fernet(key).encrypt(original)

def decrypt_data(encrypted, key):
    return Fernet(key).decrypt(encrypted)

def encrypt_file(original_file_name, encrypted_file_name, encrypt_key):
    with open(original_file_name, 'rb') as file:
        original = file.read()
    encrypted = encrypt_data(original, encrypt_key)
    # Write the encrypted data to file
    with open(encrypted_file_name, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)

def decrypt_file(encrypted_file_name, decrypted_file_name, encrypt_key):
    # Read the encrypted file
    with open(encrypted_file_name, 'rb') as enc_file:
        encrypted = enc_file.read()
    # Decrypt data with encrypt key
    decrypted = decrypt_data(encrypted, encrypt_key)
    # Write the decrypted data to file
    with open(decrypted_file_name, "wb") as dec_file:
        dec_file.write(decrypted)

def pickle_from_file(f, default_value, key = None):
    """Try to load pickled data from file `f`, return default_value on failure."""
    if not os.path.exists(f):  # File doesn't exist
        return default_value
    try:
        with open(f, "rb") as file:
            if key == None or key == "":
                loaded_data = pickle.load(file)
            else:
                encrypted_data = file.read()
                raw = decrypt_data(encrypted_data, key)
                loaded_data = pickle.loads(raw)
            # Ensure the loaded data type matches the type of default_value
            if not isinstance(loaded_data, type(default_value)):
                return default_value
            return loaded_data
    except Exception as e:
        # Handle exceptions: return default_value on failure
        print(e)
        return default_value

def pickle_to_file(f, var, key = None):
    """Try to pickle the variable `var` into file `f`, return True if successful."""
    try:
        with open(f, "wb") as file:
            if key == None or key == "":
                pickle.dump(var, file)
            else:
                raw = pickle.dumps(var)
                encrypted_data = encrypt_data(raw, key)
                file.write(encrypted_data)
        return True
    except Exception as e:
        # Handle potential exceptions
        print(e)
        return False
