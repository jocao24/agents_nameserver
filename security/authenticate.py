import secrets
import string
import time

import pyotp
import qrcode
from manage_logs.manage_logs import log_message
from utils.custom_exception import CustomException, ErrorTypes
from security.access_register import AccessRegister
from utils.pyro_config import configure_pyro

configure_pyro()


class AuthenticationManager:

    def __init__(self, password: bytes):
        self.secret = pyotp.random_base32()
        self.__generate_secret_token()
        self.access_registers = AccessRegister(password)
        self.failed_attempts = {}
        self.data = self.access_registers.load()
        self.shared_keys = {}
        self.shared_key_yp = None
        self.ip_yp_connected = None
        self.server = None

    def __generate_secret_token(self):
        token = pyotp.totp.TOTP(self.secret).provisioning_uri(name="CodeSecret", issuer_name="AccesAgent")
        img = qrcode.make(token)
        img.save("data/qrcode_access.png")

    def __verify_totp(self, otp_received):
        totp = pyotp.TOTP(self.secret)
        return totp.verify(otp_received)

    def authenticate(self, ip, otp_received: str):
        if self.__verify_totp(otp_received) is True:
            self.add_whhite_list(ip)
            log_message(f"The IP {ip} has been added to the whitelist.")
        else:
            self.failed_attempts[ip] = self.failed_attempts.get(ip, 0) + 1
            log_message(f"The IP {ip} has entered an incorrect OTP. Failed attempts: {self.failed_attempts[ip]}")
            if self.failed_attempts[ip] > 3:
                log_message(f"The IP {ip} has been blocked for multiple unsuccessful attempts.")
                raise CustomException(ErrorTypes.ip_blocked)
            else:
                log_message(f"Incorrect OTP code. Please try again.")
                raise CustomException(ErrorTypes.otp_incorrect)

    def is_blacklisted(self, ip):
        return ip in self.data['blacklist']

    def is_whitelist(self, ip):
        return ip in self.data['whitelist']

    def add_blacklist(self, ip):
        messages = []
        if self.is_blacklisted(ip):
            messages.append(f"The IP {ip} is already in the blacklist.")
            for message in messages:
                log_message(message)
            return messages
        if self.is_whitelist(ip):
            messages.append(f"The IP {ip} is in the whitelist.")
            for message in messages:
                log_message(message)
            return messages
        self.data['blacklist'].add(ip)
        self.access_registers.save(self.data)
        messages.append(f"The IP {ip} has been added to the blacklist.")
        for message in messages:
            log_message(message)
        return messages

    def add_whhite_list(self, ip):
        messages = []
        if self.is_whitelist(ip):
            messages.append(f"The IP {ip} is already in the whitelist.")
            for message in messages:
                log_message(message)
            return messages
        if self.is_blacklisted(ip):
            messages.append(f"The IP {ip} is in the blacklist.")
            for message in messages:
                log_message(message)
            return messages

        self.data['whitelist'].add(ip)
        self.access_registers.save(self.data)
        messages.append(f"The IP {ip} has been added to the whitelist.")
        for message in messages:
            log_message(message)

        return messages

    def remove_blacklist(self, ip):
        messages = []
        if self.is_blacklisted(ip):
            self.data['blacklist'].remove(ip)
            self.access_registers.save(self.data)
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
        if self.is_whitelist(ip):
            self.data['whitelist'].remove(ip)
            self.access_registers.save(self.data)
            messages.append(f"The IP {ip} has been removed from the whitelist.")
            for message in messages:
                log_message(message)
            return messages
        messages.append(f"The IP {ip} is not in the whitelist.")
        for message in messages:
            log_message(message)
        return messages

    def get_blacklist(self):
        return list(self.data['blacklist'])

    def get_whitelist(self):
        return list(self.data['whitelist'])

    def get_yellow_page_list(self):
        return list(self.data['yellow_page_list'])

    def delete(self):
        self.access_registers.delete()
        self.data = {'blacklist': set(), 'whitelist': set(), 'yellow_page_list': set()}
        self.failed_attempts = {}
        return "The data has been deleted."

    def add_yellow_page(self, ip):
        if ip not in self.data['yellow_page_list']:
            self.data['yellow_page_list'].add(ip)
            self.access_registers.save(self.data)

    def remove_yellow_page(self, ip):
        if ip in self.data['yellow_page_list']:
            self.data['yellow_page_list'].remove(ip)
            self.access_registers.save(self.data)
        else:
            return "The IP is not in the yellow_page list."

    def generate_new_key(self):
        # Longitud de la clave compartida
        key_length = 6
        # Combinar letras y números para la clave
        characters = string.ascii_letters + string.digits
        # Generar la clave
        shared_key = ''.join(secrets.choice(characters) for _ in range(key_length))
        # Tiempo de expiración en minutos
        expiration_time = time.time() + (10 * 60)  # 10 minutos desde ahora
        # Almacenar la clave y su tiempo de expiración
        self.shared_keys[shared_key] = expiration_time
        # Retornar la clave generada
        return shared_key

    def verify_shared_key(self, key):
        # Verificar si la clave existe y no ha expirado
        if key in self.shared_keys:
            if time.time() < self.shared_keys[key]:
                return True
            else:
                # La clave ha expirado
                del self.shared_keys[key]  # Eliminar clave expirada
                return False
        return False

    def register_key_shared_yp(self, key: bytes):
        self.shared_key_yp = key

    def set_ip_yp_connected(self, ip: str, server):
        self.server = server
        self.ip_yp_connected = ip

    def get_ip_yp_connected(self):
        return self.ip_yp_connected
