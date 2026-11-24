import hashlib
import hmac
import secrets


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 480_000)
    return f'{salt}${digest.hex()}'


def verify(password, stored):
    return hmac.compare_digest(stored, password_hash(password, stored.split('$', 1)[0]))
