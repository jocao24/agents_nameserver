import secrets
import string
import time
from typing import Dict


class SharedKeyManager:
    def __init__(self):
        self.shared_keys: Dict[str, float] = {}
        self.shared_key_yp = None

    def generate_shared_key(self, key_length: int = 6, expiration_minutes: int = 10) -> str:
        characters = string.ascii_letters + string.digits
        shared_key = ''.join(secrets.choice(characters) for _ in range(key_length))
        expiration_time = time.time() + (expiration_minutes * 60)
        self.shared_keys[shared_key] = expiration_time
        return shared_key

    def verify_shared_key(self, key: str) -> bool:
        if key in self.shared_keys and time.time() < self.shared_keys[key]:
            return True
        if key in self.shared_keys:
            del self.shared_keys[key]
        return False

    def register_key_shared_yp(self, key: bytes):
        self.shared_key_yp = key
