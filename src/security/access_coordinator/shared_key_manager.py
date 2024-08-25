import secrets
import string
import time
from typing import Dict

from src.manage_logs.manage_logs_v_2 import ManagementLogs
from src.security.access_coordinator.data_management import DataManagement
from src.manage_logs.manage_logs_v_2 import LogType, ComponentType

class SharedKeyManager:
    def __init__(self, management_logs: ManagementLogs):
        self.management_logs = management_logs
        self.shared_keys: Dict[str, float] = {}
        self.shared_key_yp = None
        self.data_management = DataManagement(management_logs)
        self.shared_key_agent = self.data_management.load()['ultimate_shared_key_agent']
        if not self.shared_key_agent:
            self.shared_key_agent = self.generate_shared_key()

        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'SharedKeyManager initialized', LogType.START_SESSION)

    def generate_shared_key(self, key_length: int = 6) -> str:
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Generating shared key...', LogType.KEY_GENERATION)
        characters = string.ascii_letters + string.digits
        shared_key = ''.join(secrets.choice(characters) for _ in range(key_length))
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, f'Shared key generated: {shared_key}', LogType.KEY_GENERATION)
        self.shared_key_agent = shared_key
        data = self.data_management.load()
        data['ultimate_shared_key_agent'] = shared_key
        self.data_management.save(data)
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Shared key saved', LogType.SERIALIZATION)
        return shared_key

    def get_shared_key_agent(self) -> str:
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Getting shared key...', LogType.REQUEST)
        shared_key = self.shared_key_agent
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Shared key returned', LogType.RESPONSE)
        return shared_key

    def verify_shared_key(self, key: str) -> bool:
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Verifying shared key...', LogType.VALIDATION)
        if key in self.shared_keys and time.time() < self.shared_keys[key]:
            self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Shared key verified', LogType.VALIDATION, True)
            return True
        if key in self.shared_keys:
            self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Shared key expired', LogType.VALIDATION, False)
            del self.shared_keys[key]
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Shared key not found', LogType.VALIDATION, False)
        return False

    def register_key_shared_yp(self, key: bytes):
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Registering shared key with the yellow_page...', LogType.END_REGISTRATION_YP)
        self.shared_key_yp = key
        self.management_logs.log_message(ComponentType.SHARED_KEY_MANAGER, 'Shared key registered with the yellow_page', LogType.END_REGISTRATION_YP, True)
