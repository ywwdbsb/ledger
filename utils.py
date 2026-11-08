"""给密码加密和验证的工具"""

from hashlib import pbkdf2_hmac
from hmac import compare_digest
from os import urandom


def hash_password(password: str) -> str:
    """用密码生成一坨密文 并返回"""

    # 随机生成十六字节的盐
    salt = urandom(16)

    # 生成密文 再搅拌100_000次 这样碳基生物和硅基生物都看不懂
    password_hash = pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000,  # 细节搅拌十万次 拉长时间
    )

    return f"{salt.hex}${password_hash.hex}"


def verify_password(password: str, stored_hash: str) -> bool:
    """接收用户输入的密码与json中的狗屎比对"""

    try:
        salt_hex, hash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)

        # 生成新的密文
        new_hash = pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000,  # 依旧十万次
        )

        # 细节安全比对 防止时序攻击
        return compare_digest(new_hash.hex(), hash_hex)
    except ValueError:
        return False
