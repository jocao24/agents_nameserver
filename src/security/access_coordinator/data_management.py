import os
from src.security.secure_storage import SecureStorage
from src.types.save_data_type import SaveDataType
from src.utils import get_system_uuid
from src.utils.get_system_uuid import get_system_uuid


class DataManagement:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataManagement, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, file_path: str = "data/access_data.enc"):
        if not hasattr(self, 'initialized', ):
            self.file_path = 'data/data.enc'
            self.secure_storage = SecureStorage(get_system_uuid().encode(), self.file_path)
            self._ensure_file_exists()
            self.initialized = True

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            self.save({
                'whitelist': set(),
                'blacklist': set(),
                'yellow_page_list': set(),
                'logs': '',
                'ultimate_shared_key': '',
                'ultimate_shared_key_agent': ''
            })

    def save(self, data: SaveDataType):
        data_for_storage = {
            'whitelist': list(data['whitelist']),
            'blacklist': list(data['blacklist']),
            'yellow_page_list': list(data['yellow_page_list']),
            'logs': data['logs'],
            'ultimate_shared_key': data['ultimate_shared_key'],
            'ultimate_shared_key_agent': data['ultimate_shared_key_agent']
        }
        self.secure_storage.encrypt_data(data_for_storage)

    def load(self) -> SaveDataType:
        data_from_storage = self.secure_storage.decrypt_data()
        return {
            'whitelist': set(data_from_storage['whitelist']),
            'blacklist': set(data_from_storage['blacklist']),
            'yellow_page_list': set(data_from_storage['yellow_page_list']),
            'logs': data_from_storage['logs'],
            'ultimate_shared_key': data_from_storage.get('ultimate_shared_key', ''),
            'ultimate_shared_key_agent': data_from_storage.get('ultimate_shared_key_agent', '')
        }

    def delete(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
