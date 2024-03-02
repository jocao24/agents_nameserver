import pyotp
import qrcode
from utils.custom_exception import CustomException, ErrorTypes
from security.access_register import AccessRegister
from utils.pyro_config import configure_pyro
import time

configure_pyro()


class AuthenticationManager:

    def __init__(self):
        self.secret = pyotp.random_base32()
        self.__generate_secret_token()
        self.access_registers = AccessRegister()
        self.blacklist = self.access_registers.get_register_access("Blacklist")
        self.whitelist = self.access_registers.get_register_access("Whitelist")
        self.failed_attempts = {}

    def __generate_secret_token(self):
        token = pyotp.totp.TOTP(self.secret).provisioning_uri(name="CodeSecret", issuer_name="AccesAgent")
        img = qrcode.make(token)
        img.save("qrcode_access.png")

    def __verify_totp(self, otp_received):
        totp = pyotp.TOTP(self.secret)
        return totp.verify(otp_received)

    def authenticate(self, ip, otp_received=None):
        start_time = time.time()
        if otp_received is None:
            if self.__is_blacklisted(ip):
                raise CustomException(ErrorTypes.ip_blocked)
            elif self.__is_whitelist(ip):
                return True
            else:
                end_time = time.time()
                raise CustomException(ErrorTypes.otp_required)

        elif self.__verify_totp(otp_received) is True:
            self.__add_whietelist(ip)
            return True
        else:
            self.failed_attempts[ip] = self.failed_attempts.get(ip, 0) + 1
            print("Failed attempts: ", self.failed_attempts[ip])
            if self.failed_attempts[ip] > 6:
                self.__add_blacklist(ip)
                raise CustomException(ErrorTypes.ip_blocked)
            else:
                raise CustomException(ErrorTypes.otp_incorrect)

    def __is_blacklisted(self, ip):
        return ip in self.blacklist

    def __is_whitelist(self, ip):
        return ip in self.whitelist

    def __add_blacklist(self, ip):
        self.blacklist.add(ip)
        self.access_registers.set_register_access("Blacklist", self.blacklist)

    def __add_whietelist(self, ip):
        self.whitelist.add(ip)
        self.access_registers.set_register_access("Whitelist", self.whitelist)
