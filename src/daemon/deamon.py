import Pyro5.server
import Pyro5.nameserver
import Pyro5.api

from src.daemon.data_validation import is_valid_request_data
from src.daemon.service_locator import locate_yellow_page
from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils.crypto_utils import hash_key, decrypt_data, encrypt_data
from src.types.request_data_type import RequestDataType
from src.utils.custom_exception import CustomException
from src.utils.errors import ErrorTypes
from src.utils.name_list_security import NameListSecurity


class Daemon(Pyro5.server.Daemon):
    def __init__(self, nameserver:  Pyro5.nameserver.NameServer, access_coordinator: AccessCoordinator, *args, **kwargs):
        super(Daemon, self).__init__(*args, **kwargs)
        self.nameserver = nameserver
        self.gateway_uri = None
        self.server = None
        self.access_coordinator = access_coordinator
        self.ip_yp = None
        self.access_coordinator.management_logs.log_message('Daemon -> Deamon started')

    def get_ip_entinty(self):
        return Pyro5.current_context.client_sock_addr[0]

    def get_hash_key(self, request: dict, shared_key: str, ip: str):
        id_entity = request["id"]
        key = shared_key + ip + id_entity + shared_key + ip + shared_key + ip + id_entity + shared_key
        return hash_key(key)

    def validateHandshake(self, conn, request: RequestDataType):
        id_entity = request["id"]
        self.access_coordinator.management_logs.log_message(f'Daemon -> {id_entity} -> Validating handshake request')
        try:
            shared_key_agent = 'abcd123'
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Request: {request}")
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Connection: {conn}")
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Verifying if the yellow_page is connected and Validating the request")
            self.ip_yp = self.access_coordinator.get_ip_yp_connected()
            try:
                uri_yp = locate_yellow_page(self.nameserver, self.ip_yp)
                self.server = Pyro5.api.Proxy(uri_yp)
                self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> The yellow_page is connected with the IP: {self.ip_yp}")
            except Exception as e:
                self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Error: {e}")
                raise CustomException(ErrorTypes.yp_not_registered)
            if not is_valid_request_data(request):
                self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Invalid request data")
                raise CustomException(ErrorTypes.invalid_request)

            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Request data is valid and Yellow Page is connected")

            ip_entity = conn.sock.getpeername()[0]

            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Checking IP status")
            status_ip = self.access_coordinator.check_ip_status(ip_entity)
            if status_ip.status_ip == NameListSecurity.blacklist:
                self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> The IP {ip_entity} is in the blacklist.")
                raise CustomException(ErrorTypes.ip_blocked)

            shared_key = self.get_hash_key(request, shared_key_agent, ip_entity)
            self.access_coordinator.management_logs.log_message(f"Deamon -> {id_entity} -> Decrypting data ...")
            data_decrypted = decrypt_data(request, shared_key)
            self.access_coordinator.management_logs.log_message(f"Deamon -> {id_entity} -> Data decrypted: {data_decrypted}")
            is_white = status_ip.status_ip == NameListSecurity.whitelist
            self.access_coordinator.management_logs.log_message(f"Deamon -> {id_entity} -> IP status: {status_ip.status_ip}")
            code_otp = data_decrypted.get("code_otp", None)
            if not is_white:
                self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> IP is not in the whitelist")
                if code_otp is None or code_otp == "":
                    self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> OTP is required")
                    raise CustomException(ErrorTypes.otp_required)
                self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Authenticating ...")
                self.access_coordinator.authenticate(ip_entity, code_otp)
                self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> IP authenticated")

            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Registering entity ...")
            data = {
                "data_cifrated_yp": data_decrypted["data_cifrated_yp"],
                "code_totp": code_otp,
                "shared_key": shared_key_agent,
            }
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Encrypting data ...")
            iv, data_cifrated = encrypt_data(self.access_coordinator.shared_key_yp, data)
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Data encrypted")
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Sending data to the yellow_page ...")
            self.server.request_register({
                "id": id_entity,
                "ip_entity": ip_entity,
                "iv": iv,
                "data": data_cifrated,
            })
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Key pairs generated successfully by the yellow_page")
            self.access_coordinator.server = self.server
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Redirecting to the GatewayManager ...")
            return "Hello"
        except CustomException as e:
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Error: {e}")
            raise CustomException(e.error_type)
        except Exception as e:
            self.access_coordinator.management_logs.log_message(f"Daemon -> {id_entity} -> Error: {e}")
            raise CustomException(ErrorTypes.error_unknown)
