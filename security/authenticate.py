import pyotp
import qrcode

from manage_logs.manage_logs import log_message
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

    def authenticate(self, ip, name_entity: str, type_entity: str, otp_received=None):
        if self.__is_blacklisted(ip):
            log_message(f"The {type_entity} with the IP {ip} with the name {name_entity} is blocked.")
            raise CustomException(ErrorTypes.ip_blocked)
        elif self.__is_whitelist(ip):
            return True
        if otp_received is None:
            log_message(f"The {type_entity} with the IP {ip} with the name {name_entity} is not in the whitelist. OTP required.")
            raise CustomException(ErrorTypes.otp_required)

        elif self.__verify_totp(otp_received) is True:
            self.add_whhite_list(ip)
            log_message(f"The {type_entity} with the IP {ip} with the name {name_entity} has been added to the whitelist.")
            return True
        else:
            self.failed_attempts[ip] = self.failed_attempts.get(ip, 0) + 1
            log_message(f"The {type_entity} with the IP {ip} with the name {name_entity} has entered an incorrect OTP. Failed attempts: {self.failed_attempts[ip]}")

            if self.failed_attempts[ip] > 3:
                log_message(f"The {type_entity} with the IP {ip} with the name {name_entity} has been blocked due to multiple failed attempts.")
                self.add_blacklist(ip)
                raise CustomException(ErrorTypes.ip_blocked)
            else:
                log_message(f"The {type_entity} with the IP {ip} with the name {name_entity} has entered an incorrect OTP. Failed attempts: {self.failed_attempts[ip]}")
                raise CustomException(ErrorTypes.otp_incorrect)

    def __is_blacklisted(self, ip):
        self.blacklist = self.access_registers.get_register_access("Blacklist")
        return ip in self.blacklist

    def __is_whitelist(self, ip):
        self.whitelist = self.access_registers.get_register_access("Whitelist")
        return ip in self.whitelist

    def add_blacklist(self, ip):
        messages = []
        if ip in self.blacklist:
            messages.append(f"The IP {ip} is already in the blacklist.")
            for message in messages:
                log_message(message)
            return messages
        if ip in self.whitelist:
            messages.append(f"The IP {ip} is in the whitelist.")
            for message in messages:
                log_message(message)
            return messages
        self.blacklist.add(ip)
        self.access_registers.set_register_access("Blacklist", self.blacklist)
        messages.append(f"The IP {ip} has been added to the blacklist.")
        for message in messages:
            log_message(message)
        return messages

    def add_whhite_list(self, ip):
        messages = []
        if ip in self.whitelist:
            messages.append(f"The IP {ip} is already in the whitelist.")
            for message in messages:
                log_message(message)
            return messages
        if ip in self.blacklist:
            messages.append(f"The IP {ip} is in the blacklist.")
            for message in messages:
                log_message(message)
            return messages

        self.whitelist.add(ip)
        self.access_registers.set_register_access("Whitelist", self.whitelist)
        messages.append(f"The IP {ip} has been added to the whitelist.")
        for message in messages:
            log_message(message)

        return messages

    def remove_blacklist(self, ip):
        messages = []
        if ip in self.blacklist:
            self.blacklist.remove(ip)
            self.access_registers.set_register_access("Blacklist", self.blacklist)
            messages.append(f"The IP {ip} has been removed from the blacklist.")
            for message in messages:
                log_message(message)
            return messages
        messages.append(f"The IP {ip} is not in the blacklist.")
        for message in messages:
            log_message(message)
        return messages

    def remove_whitelist(self, ip):
        messages = []
        if ip in self.whitelist:
            self.whitelist.remove(ip)
            self.access_registers.set_register_access("Whitelist", self.whitelist)
            messages.append(f"The IP {ip} has been removed from the whitelist.")
            for message in messages:
                log_message(message)
            return messages
        messages.append(f"The IP {ip} is not in the whitelist.")
        for message in messages:
            log_message(message)
        return messages

    def get_blacklist(self):
        return self.access_registers.get_register_access("Blacklist")

    def get_whitelist(self):
        return self.access_registers.get_register_access("Whitelist")

