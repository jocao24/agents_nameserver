import base64
import json
from os import urandom
from threading import Event

import time

import Pyro4
import socket

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from gateway.class_for_gateway.manage_data_gateway import ManageDataNameServer
from manage_logs.manage_logs import log_message
from security.authenticate import AuthenticationManager
from utils.errors import ErrorTypes
from utils.get_ip import get_ip
from utils.separators import show_separators, show_center_text_with_separators
from utils.validate_ip import validate_ip


class YellowPageIntegration:
    def __init__(self, yp_event: Event, finally_ns: Event, ns: Pyro4.Proxy, auth_manager: AuthenticationManager):
        self.yp_event = yp_event
        self.finally_name_server = finally_ns
        self.nameserver = ns
        self.server_uri = None
        self.server = None
        self.ip_yp = None
        self.auth_manager = auth_manager

    def _request_ip(self):
        request_ip = True
        while request_ip:
            print()
            self.ip_yp = input("Enter the IP of the yellow_page. If it is the same as the NameServer, press enter: ")
            if self.ip_yp:
                is_valid_ip = validate_ip(self.ip_yp)
                if not is_valid_ip:
                    print(ErrorTypes.invalid_ip.message)
                    log_message(ErrorTypes.invalid_ip.message)
                else:
                    request_ip = False
            else:
                self.ip_yp = get_ip()
                request_ip = False
            log_message(f"The IP of the yellow_page is: {self.ip_yp}")
            self.auth_manager.add_yellow_page(self.ip_yp)

    def get_name_device(self, ip: str):
        try:
            name = socket.gethostbyaddr(ip)
            return name[0]
        except Exception as e:
            log_message(f"An error occurred while trying to get the name of the device: {e}")
            return None

    def select_ip(self, ips: list[str]):
        i = 1
        print("")
        print(show_center_text_with_separators("Yellow Page List"))
        for ip in ips:
            name_device = self.get_name_device(ip)
            if name_device:
                print(f"{i}. {ip} - {name_device} - Active")
            else:
                print(f"{i}. {ip} - Inactive")
            i += 1
        print(show_separators())
        num_ip_sel = input("Enter the number of the yellow_page IP you want to use: ")
        if num_ip_sel.isdigit() and 0 < int(num_ip_sel) <= len(ips):
            print(show_center_text_with_separators(f"The IP {ips[int(num_ip_sel) - 1]} has been selected."))
            print("")
            return ips[int(num_ip_sel) - 1]
        else:
            print(ErrorTypes.invalid_option.message)
            return None

    def hash_key(self, key: str):
        key_complete = key + self.ip_yp + get_ip()

        # Crea una instancia del digest de hash
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())

        # Pasa los datos a hashear (necesitan estar en bytes)
        digest.update(key_complete.encode())

        # Finaliza el proceso de hash y obtiene el valor hash resultante
        hash_value = digest.finalize()

        return hash_value

    def encrypt_data(self, key, data):
        data_bytes = json.dumps(data).encode('utf-8')

        # Generar un IV aleatorio
        iv = urandom(16)

        # Crear el objeto de cifrado
        cipher = Cipher(algorithms.AES(key[:32]), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Cifrar los datos
        encrypted_data = encryptor.update(data_bytes) + encryptor.finalize()

        # Retornar el IV y los datos cifrados (ambos necesarios para el descifrado)

        iv_base64 = base64.b64encode(iv).decode()
        encrypted_data_base64 = base64.b64encode(encrypted_data).decode()

        return iv_base64, encrypted_data_base64

    def config_ip(self):
        time.sleep(1)
        ips = self.auth_manager.get_yellow_page_list()
        while True:
            print(show_separators())
            print(show_center_text_with_separators("Yellow Page Configuration"))
            if ips and len(ips) > 0:
                opt_select = input("Do you want to use the yellow_page IP saved in the file? (y/n): -> default y ")
                if opt_select.lower() == 'y' or opt_select == '':
                    self.ip_yp = self.select_ip(ips)
                    if not self.ip_yp:
                        print(ErrorTypes.invalid_option.message)
                        continue
                elif opt_select.lower() == 'n':
                    self._request_ip()

                else:
                    print(ErrorTypes.invalid_option.message)
                    continue
                break
            else:
                self._request_ip()
                break

        self.auth_manager.add_yellow_page(self.ip_yp)
        message = f"Wating for the yellow_page to be registered in the device {self.get_name_device(self.ip_yp)}..."
        print(message)
        found_yp = self.check_server(message, 2, 50)
        if found_yp:
            print("Yellow Page Found and Active")
            while True:
                # Se le pide que ingrese la key compartida
                key_shared = input("Enter the shared key provided by the yellow_page: ")
                if key_shared:
                    key_shared_com = key_shared + self.ip_yp + get_ip() + key_shared + self.get_name_device(get_ip()) + key_shared
                    key_shared_com_hash = self.hash_key(key_shared_com)
                    data = {
                        "message": "ping"
                    }
                    try:
                        iv, encrypted_data = self.encrypt_data(key_shared_com_hash, data)
                        data = self.server.ping(iv, encrypted_data)
                        if data and data.get('message') == 'pong':
                            print("The shared key has been correctly validated.")
                            self.auth_manager.shared_key_yp = key_shared_com_hash
                            break
                        else:
                            print("The shared key is not correct. Please try again.")
                    except Exception as e:
                        print(f"An error occurred while trying to connect to the yellow_page: {e}")
                        log_message(f"An error occurred while trying to connect to the yellow_page: {e}")
            print(show_separators())
            print(show_center_text_with_separators("The yellow_page has been correctly configured"))
            print("\n")
            self.yp_event.set()
        else:
            print(show_separators())
            print(show_center_text_with_separators("The yellow_page is not registered or is not active."))
            print("\n")
            self.finally_name_server.set()

    def check_server(self, message: str, time_sleep: int = 1, max_attempts: int = 10):
        log_message(message)
        found_yellow_page = False
        self.server_uri = None
        while self.server_uri is None and max_attempts > 0:
            try:
                name_yellow_page = 'yellow_page@' + self.ip_yp
                self.server_uri = self.nameserver.lookup(name_yellow_page)
                self.server = Pyro4.Proxy(self.server_uri)

                if self.server_uri:
                    self.auth_manager.set_ip_yp_connected(self.ip_yp, self.server)
                    message = f"The device {self.get_name_device(self.ip_yp)} has been correctly configured as yellow_page."
                    log_message(message)
                    print(message)
                    found_yellow_page = True

            except Pyro4.errors.NamingError:
                log_message(ErrorTypes.yellow_page_not_found.message)
            except Exception as e:
                log_message(f"An error occurred while trying to connect to the yellow_page: {e}")
            finally:
                max_attempts -= 1

            time.sleep(time_sleep)

        return found_yellow_page

    def is_up_yellow_page(self):
        message = f"Wating for the yellow_page to be registered at {self.ip_yp}..."
        found_yp = self.check_server(message, 1, 10)
        if not found_yp:
            message = "The yellow_page is not registered or is not active."
            log_message(message)
            raise Pyro4.errors.CommunicationError(message)
        return found_yp
