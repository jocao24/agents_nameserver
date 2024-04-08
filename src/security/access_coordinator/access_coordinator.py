from src.manage_logs.manage_logs import log_message
from src.security.access_coordinator.ip_manager import IPManager
from src.security.access_coordinator.shared_key_manager import SharedKeyManager
from src.security.access_coordinator.totp_manager import TOTPManager
from src.utils.custom_exception import CustomException
from src.utils.errors import ErrorTypes
from src.utils.name_list_security import NameListSecurity


class AccessCoordinator(TOTPManager, IPManager, SharedKeyManager):
    def __init__(self, password: bytes):
        TOTPManager.__init__(self)
        IPManager.__init__(self, password)
        SharedKeyManager.__init__(self)
        self.failed_login_attempts = {}
        self.ip_yp_connected = None
        self.server = None

    def set_ip_yp_connected(self, ip: str, server):
        self.server = server
        self.ip_yp_connected = ip

    def get_ip_yp_connected(self):
        return self.ip_yp_connected

    def authenticate(self, ip: str, otp_received: str):
        if not self.verify_totp(otp_received):
            self.failed_login_attempts[ip] = self.failed_login_attempts.get(ip, 0) + 1
            log_message(f"The IP {ip} has entered an incorrect OTP. Failed attempts: {self.failed_login_attempts[ip]}")
            if self.failed_login_attempts[ip] > 3:
                log_message(f"The IP {ip} has been blocked for multiple unsuccessful attempts.")
                raise CustomException(ErrorTypes.ip_blocked)
            else:
                log_message("Incorrect OTP code. Please try again.")
                raise CustomException(ErrorTypes.otp_incorrect)
        self.add_ip_to_list(ip, NameListSecurity.whitelist)
        log_message(f"The IP {ip} has been added to the whitelist.")
        return ErrorTypes.ok
