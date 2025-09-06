# from cryptography.fernet import Fernet

# FERNET_KEY = b'BAim6q38GF8ecFfoPYT23o8e6QQ003MZifgpn8uLFWY='  # Replace with a real one
# cipher = Fernet(FERNET_KEY)


# def encrypt_message(message: str) -> bytes:
#     return cipher.encrypt(message.encode())


# def decrypt_message(encrypted: bytes) -> str:
#     return cipher.decrypt(encrypted).decode()


# # Comment the above code and use this to generate a new key:
# # from cryptography.fernet import Fernet
# # print(Fernet.generate_key())

"""
shared/encrypt.py

Provides symmetric-key encryption/decryption for chat messages
using cryptography.fernet (AES-CBC with HMAC).
"""

from cryptography.fernet import Fernet

# ─────────────────────────────────────────────────────────────────────────────
# Replace this with your own Fernet key. To generate a new one, run:
#   >>> from cryptography.fernet import Fernet
#   >>> print(Fernet.generate_key())
#
FERNET_KEY = b"BAim6q38GF8ecFfoPYT23o8e6QQ003MZifgpn8uLFWY="
# ─────────────────────────────────────────────────────────────────────────────

# Initialize the Fernet cipher once
_cipher = Fernet(FERNET_KEY)


def encrypt_message(message: str) -> bytes:
    """
    Encrypts a UTF-8 string into a Fernet token (bytes).
    Usage:
        token = encrypt_message("hello")
        # send token over socket...
    """
    if not isinstance(message, str):
        raise TypeError("encrypt_message expects a str")
    return _cipher.encrypt(message.encode("utf-8"))


def decrypt_message(token: bytes) -> str:
    """
    Decrypts a Fernet token back into the original UTF-8 string.
    Usage:
        plaintext = decrypt_message(token)
    """
    if not isinstance(token, (bytes, bytearray)):
        raise TypeError("decrypt_message expects bytes")
    return _cipher.decrypt(token).decode("utf-8")


# Optional helper (uncomment to use):
# def generate_new_key() -> bytes:
#     """
#     Generates and returns a fresh Fernet key.
#     Print it out and copy into FERNET_KEY above.
#     """
#     return Fernet.generate_key()

# call the function encrypt_message to test
# if __name__ == "__main__":
#     test_message = "Hello, World!"
#     encrypted = encrypt_message(test_message)
#     print(f"Encrypted: {encrypted}")

#     decrypted = decrypt_message(encrypted)
#     print(f"Decrypted: {decrypted}")

#     assert decrypted == test_message, "Decryption failed!"
#     print("Encryption/Decryption test passed!")
