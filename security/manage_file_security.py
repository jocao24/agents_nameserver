import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from utils.custom_exception import CustomException
from utils.errors import ErrorTypes
from utils.types.save_data_type import SaveDataType


def derive_key(password: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512_256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password))


def encrypt_file(file_path: str, password: bytes, data: SaveDataType):
    try:
        salt = os.urandom(16)
        key = derive_key(password, salt)
        f = Fernet(key)

        # Convierte el diccionario a una cadena JSON.
        data_str = json.dumps({
            "whitelist": list(data['whitelist']),
            "blacklist": list(data['blacklist']),
            "yellow_page_list": list(data['yellow_page_list'])
        })

        encrypted_data = f.encrypt(data_str.encode())

        # Si no existe el archivo o el directorio, lo crea.
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        with open(file_path, 'wb') as file:
            file.write(salt + encrypted_data)
    except Exception:
        raise CustomException(ErrorTypes.error_encryption)


def decrypt_file(file_path: str, password: bytes) -> SaveDataType or None:
    try:
        with open(file_path, 'rb') as file:
            salt = file.read(16)
            data = file.read()

        key = derive_key(password, salt)
        f = Fernet(key)

        decrypted_data = f.decrypt(data)
        if decrypted_data is None:
            return None
        data_decoded = decrypted_data.decode()
        return {
            "whitelist": set(json.loads(data_decoded)["whitelist"]),
            "blacklist": set(json.loads(data_decoded)["blacklist"]),
            "yellow_page_list": set(json.loads(data_decoded)["yellow_page_list"])
        }

    except Exception:
        raise CustomException(ErrorTypes.password_incorrect)

