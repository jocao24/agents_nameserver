import Pyro4

from src.daemon.data_validation import is_valid_request_data
from src.daemon.service_locator import locate_yellow_page
from src.manage_logs.manage_logs import log_message
from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils.crypto_utils import hash_key, decrypt_data, encrypt_data
from src.types.request_data_type import RequestDataType
from src.utils.custom_exception import CustomException
from src.utils.errors import ErrorTypes
from src.utils.name_list_security import NameListSecurity


class Daemon(Pyro4.Daemon):
    def __init__(self, nameserver: Pyro4.Proxy, access_coordinator: AccessCoordinator, *args, **kwargs):
        super(Daemon, self).__init__(*args, **kwargs)
        self.nameserver = nameserver
        self.gateway_uri = None
        self.server = None
        self.access_coordinator = access_coordinator
        self.ip_yp = None

    def get_ip_entinty(self):
        return Pyro4.current_context.client_sock_addr[0]

    def get_hash_key(self, request: dict, shared_key: str, ip: str):
        id_entity = request["id"]
        key = shared_key + ip + id_entity + shared_key + ip + shared_key + ip + id_entity + shared_key
        return hash_key(key)

    def validateHandshake(self, conn, request: RequestDataType):
        print("The deamon intercepts the call request to the gateway manager")
        print("----------------------------------------------------------")
        try:
            shared_key_agent = 'abcd123'

            print("1. The yp is verified to be connected")
            self.ip_yp = self.access_coordinator.get_ip_yp_connected()
            try:
                uri_yp = locate_yellow_page(self.nameserver, self.ip_yp)
                self.server = Pyro4.Proxy(uri_yp)
            except Exception as e:
                log_message(f"Error: {e}")
                raise CustomException(ErrorTypes.yp_not_registered)
            print("The yp is ok to be connected")
            print("-----------------------------------------------------------------")

            print("Start the handshake validation process")
            if not is_valid_request_data(request):
                print("The request is invalid")
                raise CustomException(ErrorTypes.invalid_request)
            print("The request is valid")
            print("-----------------------------------------------------------------")

            id_entity = request["id"]
            ip_entity = conn.sock.getpeername()[0]

            print("The entity id is: ", id_entity)
            status_ip = self.access_coordinator.check_ip_status(ip_entity)
            if status_ip.status_ip == NameListSecurity.blacklist:
                log_message(f"{status_ip.message}")
                raise CustomException(ErrorTypes.ip_blocked)
            print("The ip is not in the blacklist")

            shared_key = self.get_hash_key(request, shared_key_agent, ip_entity)
            data_decrypted = decrypt_data(request, shared_key)
            is_white = status_ip.status_ip == NameListSecurity.whitelist
            code_otp = data_decrypted.get("code_otp", None)
            if not is_white:
                if code_otp is None or code_otp == "":
                    raise CustomException(ErrorTypes.otp_required)
                self.access_coordinator.authenticate(ip_entity, code_otp)

            print("The entity is authenticated")

            data = {
                "data_cifrated_yp": data_decrypted["data_cifrated_yp"],
                "code_totp": code_otp,
                "shared_key": shared_key_agent,
            }
            print("The data sent to the yp is: ", data)
            iv, data_cifrated = encrypt_data(self.access_coordinator.shared_key_yp, data)
            self.server.request_register({
                "id": id_entity,
                "ip_entity": ip_entity,
                "iv": iv,
                "data": data_cifrated,
            })
            self.access_coordinator.server = self.server
            print("The data is sent successfully to the yp")
            return "Hello"
        except CustomException as e:
            raise CustomException(e.error_type)
        except Exception as e:
            raise CustomException(ErrorTypes.error_unknown)
