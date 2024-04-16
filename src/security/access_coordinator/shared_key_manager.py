import secrets
import string
import time
from typing import Dict

from src.manage_logs.manage_logs import ManagementLogs
from src.security.access_coordinator.data_management import DataManagement


class SharedKeyManager:
    def __init__(self, management_logs: ManagementLogs):
        self.management_logs = management_logs
        self.shared_keys: Dict[str, float] = {}
        self.shared_key_yp = None
        self.data_management = DataManagement(management_logs)
        self.shared_key_agent = self.data_management.load()['ultimate_shared_key_agent']
        if not self.shared_key_agent:
            self.shared_key_agent = self.generate_shared_key()

        self.management_logs.log_message('SharedKeyManager -> SharedKeyManager initialized')

    def generate_shared_key(self, key_length: int = 6) -> str:
        self.management_logs.log_message('SharedKeyManager -> Generating shared key...')
        characters = string.ascii_letters + string.digits
        shared_key = ''.join(secrets.choice(characters) for _ in range(key_length))
        self.management_logs.log_message(f'SharedKeyManager -> Shared key generated: {shared_key}')
        self.shared_key_agent = shared_key
        data = self.data_management.load()
        data['ultimate_shared_key_agent'] = shared_key
        self.data_management.save(data)
        return shared_key

    def get_shared_key_agent(self) -> str:
        self.management_logs.log_message('SharedKeyManager -> Getting shared key...')
        shared_key = self.shared_key_agent
        self.management_logs.log_message('SharedKeyManager -> Shared key returned')
        return shared_key

    def verify_shared_key(self, key: str) -> bool:
        self.management_logs.log_message('SharedKeyManager -> Verifying shared key...')
        if key in self.shared_keys and time.time() < self.shared_keys[key]:
            self.management_logs.log_message('SharedKeyManager -> Shared key verified')
            return True
        if key in self.shared_keys:
            self.management_logs.log_message('SharedKeyManager -> Shared key expired')
            del self.shared_keys[key]
        self.management_logs.log_message('SharedKeyManager -> Shared key not found')
        return False

    def register_key_shared_yp(self, key: bytes):
        self.management_logs.log_message('SharedKeyManager -> Registering shared key with the yellow_page...')
        self.shared_key_yp = key
        self.management_logs.log_message('SharedKeyManager -> Shared key registered with the yellow_page')
