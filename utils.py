from hashlib import pbkdf2_hmac
from hmac import compare_digest
from os import urandom


def hash_password(password: str) -> str:
    salt = urandom(16)
    password_hash = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex}${password_hash.hex}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        new_hash = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return compare_digest(new_hash.hex(), hash_hex)
    except ValueError:
        return False
