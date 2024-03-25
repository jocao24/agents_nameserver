import base64
import hashlib
import uuid
from os import urandom
from typing import TypedDict

import Pyro4
from Pyro4.errors import NamingError
from Pyro4.util import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from gateway.class_for_gateway.manage_data_gateway import ManageDataNameServer
from manage_logs.manage_logs import log_message
from security.authenticate import AuthenticationManager
from utils.custom_exception import CustomException
from utils.errors import ErrorTypes
from utils.types.agent_nameserver_type import AgentNSType
from utils.types.client_nameserver_type import ClientNSType


class PublicData(TypedDict):
    id: str
    ip: str


class PrivateData(TypedDict):
    iv: str
    data: str


class RequestDataType(TypedDict):
    iv: str
    data: str
    id: str


class SecureDaemon(Pyro4.Daemon):
    def __init__(self, nameserver: Pyro4.Proxy, auth_manager: AuthenticationManager, *args, **kwargs):
        super(SecureDaemon, self).__init__(*args, **kwargs)
        self.nameserver = nameserver
        self.gateway_uri = None
        self.server = None
        self.auth_manager = auth_manager
        self.ip_yp = None

    def remove_duplicate_entities(self):
        try:
            # Fetch the current list of registered objects in the nameserver
            registered_objects = self.nameserver.list()

            # Dictionary to track the seen ids and names
            seen_ids_names = {}

            # Iterate through the registered objects to identify and remove duplicates
            try:
                for name, uri in registered_objects.items():
                    # Extracting the id and name based on your specific identifier structure
                    parts = name.split("-")
                    if len(parts) <= 1:
                        continue  # Skip this element if it does not follow the expected format

                    # Check if the unique identifier has already been processed
                    if name in seen_ids_names:
                        # If it exists, it"s considered a duplicate and should be removed
                        try:
                            log_message(f"Removing duplicate: {name} with URI {uri}")
                            self.nameserver.remove(name)
                        except NamingError as e:
                            # print(f"Error removing duplicate {name}: {e}")
                            log_message(f"Error removing duplicate {name}: {e}")
                    else:
                        # If it"s not a duplicate, add it to the seen ids and names
                        seen_ids_names[name] = name
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    def locate_gateway(self):
        list_nameserver = self.nameserver.list()
        for name, uri in list_nameserver.items():
            if "gateway_manager" in name:
                self.gateway_uri = uri
                break

    def locate_yellow_page(self):
        try:
            self.ip_yp = self.auth_manager.get_ip_yp_connected()
            list_nameserver = self.nameserver.list()
            name_yp = "yellow_page@" + self.ip_yp
            for name, uri in list_nameserver.items():
                if name_yp in name:
                    self.server = Pyro4.Proxy(uri)
                    break

        except Exception as e:
            print(f"Error: {e}")

    def get_ip_entinty(self):
        return Pyro4.current_context.client_sock_addr[0]

    def is_valid_request_data(self, request: RequestDataType) -> bool:
        if not isinstance(request, dict):
            return False
        if "iv" not in request or "data" not in request or "id" not in request:
            return False
        return True

    def hash_key(self, key: str):

        # Crea una instancia del digest de hash
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())

        # Pasa los datos a hashear (necesitan estar en bytes)
        digest.update(key.encode())

        # Finaliza el proceso de hash y obtiene el valor hash resultante
        hash_value = digest.finalize()

        return hash_value

    def encrypt_data(self, data):
        try:
            data_bytes = json.dumps(data).encode("utf-8")

            # Generar un IV aleatorio
            iv = urandom(16)

            # Crear el objeto de cifrado
            cipher = Cipher(algorithms.AES(self.auth_manager.shared_key_yp[:32]), modes.CFB(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # Cifrar los datos
            encrypted_data = encryptor.update(data_bytes) + encryptor.finalize()

            # Retornar el IV y los datos cifrados (ambos necesarios para el descifrado)

            iv_base64 = base64.b64encode(iv).decode()
            encrypted_data_base64 = base64.b64encode(encrypted_data).decode()

            return iv_base64, encrypted_data_base64
        except Exception as e:
            print(f"Error: {e}")

    def validateHandshake(self, conn, request: RequestDataType):
        try:
            self.locate_yellow_page()
            # Verifico que sea de tipo RequestDataType
            if not self.is_valid_request_data(request):
                raise CustomException(ErrorTypes.invalid_request)

            id = request["id"]
            # <socket.socket fd=1560, family=2, type=1, proto=0, laddr=('192.168.1.10', 9091), raddr=('192.168.1.10', 49629)>
            ip = conn.sock.getpeername()[0]

            # Se verifica si la ip esta en la lista blanca
            is_black = self.auth_manager.is_blacklisted(ip)
            if is_black:
                raise CustomException(ErrorTypes.ip_blocked)

            iv_base64 = request["iv"]
            data_base64 = request["data"]

            # Se convierten los datos a bytes
            iv = base64.b64decode(iv_base64)
            data = base64.b64decode(data_base64)

            shared_key = "abcd123"
            #  ip + self.id_agent + shared_key + code_otp + ip + self.id_agent + shared_key
            key = ip + id + shared_key + ip + id + shared_key
            hash_key = self.hash_key(key)

            # Se descifra el iv y los datos
            cipher = Cipher(algorithms.AES(hash_key[:32]), modes.CFB(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(data) + decryptor.finalize()
            print(f"\nData decrypted: \n{decrypted_data}")

            data_decrypted = json.loads(decrypted_data.decode("utf-8"))
            print(f"\nData decrypted: \n{data_decrypted}")
            # is_white = self.auth_manager.is_whitelist(ip)
            # Si no esta en la lista blanca se verifica que venia con un codigo otp
            '''
                        if not is_white:
                           if 'otp' not in data_decrypted:
                               raise CustomException(ErrorTypes.otp_required)
                           otp = data_decrypted['otp']
                           self.auth_manager.authenticate(ip, otp)

                        '''

            # Se toma la public key del agente y se encripta con la key compartida
            public_key = data_decrypted["public_key"]

            # Se encripta la public key con la key compartida
            iv, encrypted_data = self.encrypt_data({
                "public_key": public_key
            })
            self.server.request_register({
                "id": id,
                "ip": ip,
                "iv": iv,
                "data": encrypted_data,
            })
            return "Hello"
        except CustomException as e:
            print(f"Error: {e}")
            conn.sock.sendall(False)
        except Exception as e:
            print(f"Error: {e}")
            conn.sock.sendall(False)
