import os
from src.security.secure_storage import SecureStorage
from src.types.save_data_type import SaveDataType


class AccessListKeeper:
    def __init__(self, password: bytes, file_path: str = "data/access_data.enc"):
        self.file_path = file_path
        self.secure_storage = SecureStorage(password, file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            self.save({
                'whitelist': set(),
                'blacklist': set(),
                'yellow_page_list': set()
            })

    def save(self, data: SaveDataType):
        # Convert sets to lists for JSON serialization
        data_for_storage = {
            'whitelist': list(data['whitelist']),
            'blacklist': list(data['blacklist']),
            'yellow_page_list': list(data['yellow_page_list'])
        }
        self.secure_storage.encrypt_data(data_for_storage)

    def load(self) -> SaveDataType:
        data_from_storage = self.secure_storage.decrypt_data()
        return {
            'whitelist': set(data_from_storage['whitelist']),
            'blacklist': set(data_from_storage['blacklist']),
            'yellow_page_list': set(data_from_storage['yellow_page_list'])
        }

    def delete(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
