import base64
from os import urandom
from Pyro4.util import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from src.manage_logs.manage_logs import ManagementLogs
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
        self.management_logs.log_message('AccessCoordinator -> AccessCoordinator initialized')

    def set_ip_yp_connected(self, ip: str, server):
        self.server = server
        self.ip_yp_connected = ip

    def get_ip_yp_connected(self):
        return self.ip_yp_connected

    def authenticate(self, ip: str, otp_received: str):
        self.management_logs.log_message(f"AccessCoordinator -> Authenticating IP: {ip}")
        if not self.verify_totp(otp_received):
            self.failed_login_attempts[ip] = self.failed_login_attempts.get(ip, 0) + 1
            self.management_logs.log_message(f"AccessCoordinator -> The IP {ip} has entered an incorrect OTP. Failed attempts: {self.failed_login_attempts[ip]}")
            if self.failed_login_attempts[ip] > 3:
                self.management_logs.log_message(f"AccessCoordinator -> The IP {ip} has been blocked for multiple unsuccessful attempts.")
                raise CustomException(ErrorTypes.ip_blocked)
            else:
                self.management_logs.log_message("AccessCoordinator -> Incorrect OTP code. Please try again.")
                raise CustomException(ErrorTypes.otp_incorrect)
        self.add_ip_to_list(ip, NameListSecurity.whitelist)
        self.management_logs.log_message(f"AccessCoordinator -> The IP {ip} has been added to the whitelist.")
        return ErrorTypes.ok

    def validate_shared_key(self, ip_yp=None, request_key=False):
        self.management_logs.log_message("AccessCoordinator -> Validating the shared key...")
        data_to_save = self.access_list_keeper.load()
        key = data_to_save['ultimate_shared_key']
        if not ip_yp:
            ip_yp = self.ip_yp_connected
        if request_key:
            key = None
        while True:
            if not key:
                key = input("Enter the shared key provided by the yellow_page: ")
            if key:
                key_shared_com = (key + ip_yp + get_ip() + key + get_name_device(get_ip(), self.management_logs) + key)
                key_shared_com_hash = self.hash_key_yp(key_shared_com, ip_yp)
                data = {"message": "ping"}
                try:
                    iv, encrypted_data = self.encrypt_data_by_yp(key_shared_com_hash, data)
                    response = self.server.ping(iv, encrypted_data)
                    if response and response.get('message') == 'pong':
                        self.management_logs.log_message("The shared key has been correctly validated.")
                        print("The shared key has been correctly validated.")
                        data_to_save['ultimate_shared_key'] = key
                        self.access_list_keeper.save(data_to_save)
                        self.shared_key_yp = key_shared_com_hash
                        return True
                except Exception as e:
                    print(f"An error occurred while trying to connect to the yellow_page: {e}")
                    self.management_logs.log_message(f"AccessCoordinator -> The shared key is not correct. Please try again. Error: {e}")
            else:
                self.management_logs.log_message("The shared key is not correct. Please try again.")
                print("The shared key is not correct. Please try again.")

    def hash_key_yp(self, key: str, ip_yp: str):
        self.management_logs.log_message("AccessCoordinator -> Hashing the shared key...")
        key_complete = key + ip_yp + get_ip()
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key_complete.encode())
        hash_value = digest.finalize()
        self.management_logs.log_message("AccessCoordinator -> The shared key has been hashed.")
        return hash_value

    def encrypt_data_by_yp(self, key, data):
        self.management_logs.log_message("AccessCoordinator -> Encrypting data2 by the yellow_page...")
        data_bytes = json.dumps(data).encode('utf-8')
        iv = urandom(16)
        cipher = Cipher(algorithms.AES(key[:32]), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data_bytes) + encryptor.finalize()
        self.management_logs.log_message("AccessCoordinator -> Data encrypted by the yellow_page.")
        iv_base64 = base64.b64encode(iv).decode()
        encrypted_data_base64 = base64.b64encode(encrypted_data).decode()
        return iv_base64, encrypted_data_base64
