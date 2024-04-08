from src.security.cryptography.crypto_utils import decrypt_data, encrypt_data, hash_key
from src.utils.custom_exception import CustomException
from src.utils.errors import ErrorTypes
from src.types.request_data_type import RequestDataType


def is_valid_request_data(request: RequestDataType) -> bool:
    return all(k in request for k in ["iv", "data", "id"])