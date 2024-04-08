import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureStorage:
    def __init__(self, password: bytes, file_path: str = None):
        self.password = password
        self.file_path = file_path

    def __derive_key(self, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512_256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(self.password))

    def encrypt_data(self, data):
        salt = os.urandom(16)
        key = self.__derive_key(salt)
        fernet = Fernet(key)

        data_str = json.dumps(data)
        encrypted_data = fernet.encrypt(data_str.encode())

        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path))

        with open(self.file_path, 'wb') as file:
            file.write(salt + encrypted_data)

    def decrypt_data(self):
        if self.file_path is None:
            raise ValueError("file_path must be specified")
        file_path = self.file_path

        with open(file_path, 'rb') as file:
            salt = file.read(16)
            encrypted_data = file.read()

        key = self.__derive_key(salt)
        fernet = Fernet(key)

        decrypted_data = fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
