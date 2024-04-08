import base64
from os import urandom
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from Pyro4.util import json


def hash_key(key: str) -> bytes:
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(key.encode())
    return digest.finalize()


def encrypt_data(shared_key: bytes, data: dict) -> (str, str):
    data_bytes = json.dumps(data).encode("utf-8")
    iv = urandom(16)
    cipher = Cipher(algorithms.AES(shared_key[:32]), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(data_bytes) + encryptor.finalize()
    return base64.b64encode(iv).decode(), base64.b64encode(encrypted_data).decode()


def decrypt_data(request: dict, shared_key: bytes) -> dict:
    iv = base64.b64decode(request["iv"])
    data = base64.b64decode(request["data"])
    cipher = Cipher(algorithms.AES(shared_key[:32]), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(data) + decryptor.finalize()
    return json.loads(decrypted_data.decode("utf-8"))
