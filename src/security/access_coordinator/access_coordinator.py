import base64
from os import urandom
from Pyro4.util import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from src.manage_logs.manage_logs_v_2 import ComponentType, LogType, ManagementLogs
from src.security.access_coordinator.ip_manager import IPManager
from src.security.access_coordinator.shared_key_manager import SharedKeyManager
from src.security.access_coordinator.totp_manager import TOTPManager
from src.utils.custom_exception import CustomException
from src.utils.errors import ErrorTypes
from src.utils.get_name_device import get_name_device
from src.utils.name_list_security import NameListSecurity
from src.utils.get_ip import get_ip

class AccessCoordinator(TOTPManager, IPManager, SharedKeyManager):
    def __init__(self, management_logs: ManagementLogs):
        TOTPManager.__init__(self, management_logs)
        IPManager.__init__(self, management_logs)
        SharedKeyManager.__init__(self, management_logs)
        self.failed_login_attempts = {}
        self.ip_yp_connected = None
        self.server = None
        self.management_logs = management_logs
        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, 'AccessCoordinator initialized', LogType.START_SESSION)

    def set_ip_yp_connected(self, ip: str, server):
        self.server = server
        self.ip_yp_connected = ip

    def get_ip_yp_connected(self):
        return self.ip_yp_connected

    def authenticate(self, ip: str, otp_received: str):
        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, f"Authenticating IP: {ip}", LogType.AUTHENTICATION)
        if not self.verify_totp(otp_received):
            self.failed_login_attempts[ip] = self.failed_login_attempts.get(ip, 0) + 1
            self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, f"The IP {ip} has entered an incorrect OTP. Failed attempts: {self.failed_login_attempts[ip]}", LogType.AUTHENTICATION, False)
            if self.failed_login_attempts[ip] > 3:
                self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, f"The IP {ip} has been blocked for multiple unsuccessful attempts.", LogType.AUTHENTICATION, False)
                raise CustomException(ErrorTypes.ip_blocked)
            else:
                self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "Incorrect OTP code. Please try again.", LogType.AUTHENTICATION, False)
                raise CustomException(ErrorTypes.otp_incorrect)
        self.add_ip_to_list(ip, NameListSecurity.whitelist)
        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, f"The IP {ip} has been added to the whitelist.", LogType.AUTHENTICATION)
        return ErrorTypes.ok

    def validate_shared_key(self, ip_yp=None, request_key=False):
        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "Validating the shared key...", LogType.VALIDATION)
        data_to_save = self.access_list_keeper.load()
        shared_key = data_to_save['ultimate_shared_key']
        if not ip_yp:
            ip_yp = self.ip_yp_connected
        if request_key:
            shared_key = None
        while True:
            if not shared_key:
                shared_key = input("Enter the shared key provided by the yellow_page: ")
            if shared_key:
                name_device = get_name_device(get_ip(), self.management_logs)
                ip_ns =  get_ip()
                key_shared_com = (shared_key + ip_yp + ip_ns + shared_key + name_device + shared_key + get_ip() + ip_yp)
                key_shared_com_hash = self.hash_key_yp(key_shared_com)
                data = {"message": "ping"}
                try:
                    iv, encrypted_data = self.encrypt_data_by_yp(key_shared_com_hash, data)
                    response = self.server.ping(iv, encrypted_data, get_name_device(get_ip(), self.management_logs))
                    if response and response.get('message') == 'pong':
                        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "The shared key has been correctly validated.", LogType.VALIDATION)
                        print("The shared key has been correctly validated.")
                        data_to_save['ultimate_shared_key'] = shared_key
                        self.access_list_keeper.save(data_to_save)
                        self.shared_key_yp = key_shared_com_hash
                        return True
                    else:
                        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "The shared key is not correct. Please try again.", LogType.VALIDATION, False)
                        print("The shared key is not correct. Please try again.")
                        shared_key = None
                except Exception as e:
                    print(f"An error occurred while trying to connect to the yellow_page: {e}")
                    self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, f"The shared key is not correct. Please try again. Error: {e}", LogType.VALIDATION, False)
                    shared_key = None
            else:
                self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "The shared key is not correct. Please try again.", LogType.VALIDATION, False)
                print("The shared key is not correct. Please try again.")

    def hash_key_yp(self, key: str):
        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "Hashing the shared key...", LogType.SHARED_KEY)
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key.encode())
        hash_value = digest.finalize()
        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "The shared key has been hashed.", LogType.SHARED_KEY)
        return hash_value

    def encrypt_data_by_yp(self, key, data):
        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "Encrypting data by the yellow_page...", LogType.ENCRYPTION)
        data_bytes = json.dumps(data).encode('utf-8')
        iv = urandom(16)
        cipher = Cipher(algorithms.AES(key[:32]), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data_bytes) + encryptor.finalize()
        self.management_logs.log_message(ComponentType.ACCESS_COORDINATOR, "Data encrypted by the yellow_page.", LogType.ENCRYPTION)
        iv_base64 = base64.b64encode(iv).decode()
        encrypted_data_base64 = base64.b64encode(encrypted_data).decode()
        return iv_base64, encrypted_data_base64
