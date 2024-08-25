from concurrent.futures import Future
import queue
import threading
import time
import Pyro4
from Pyro4.errors import NamingError

from src.daemon.data_validation import is_valid_request_data
from src.daemon.service_locator import locate_yellow_page
from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils import get_name_device
from src.utils.crypto_utils import hash_key, decrypt_data, encrypt_data
from src.types.request_data_type import RequestDataType
from src.utils.custom_exception import CustomException
from src.utils.errors import ErrorTypes
from src.utils.name_list_security import NameListSecurity
from src.manage_logs.manage_logs_v_2 import LogType, ComponentType, ManagementLogs
from src.utils.emmit_log import log_execution_time, log_execution_time_with_message

class Daemon(Pyro4.Daemon):
    def __init__(self, nameserver: Pyro4.Proxy, access_coordinator: AccessCoordinator, *args, **kwargs):
        super(Daemon, self).__init__(*args, **kwargs)
        self.nameserver = nameserver
        self.gateway_uri = None
        self.server = None
        self.access_coordinator = access_coordinator
        self.ip_yp = None
        log_execution_time(self.access_coordinator.management_logs, 'Daemon -> Daemon started', LogType.START_SESSION, ComponentType.DAEMON, time=0, uuid_agent=0)

    def get_ip_entinty(self):
        return Pyro4.current_context.client_sock_addr[0]

    def get_hash_key(self, request: dict, shared_key: str, ip: str):
        id_entity = request["id"]
        key = shared_key + ip + id_entity + shared_key + ip + shared_key + ip + id_entity + shared_key
        return hash_key(key)

    def validateHandshake(self, conn, request: RequestDataType):
        id_entity = request.get("id", None)
        
        
        start_time = time.perf_counter()
        log_execution_time(self.access_coordinator.management_logs, f'Daemon -> {id_entity} -> Validating handshake request', LogType.REQUEST, ComponentType.DAEMON, time=0, uuid_agent=id_entity)

        try:
            shared_key_agent = 'abcd123'

            start_time = time.perf_counter()
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Request: {request}", LogType.REQUEST_INFO, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "REQUEST", LogType.REQUEST_INFO, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Connection: {conn}", LogType.CONNECTION_DEAMON_INFO, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "REQUEST_INFO", LogType.CONNECTION_DEAMON_INFO, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Verifying if the yellow_page is connected and Validating the request", LogType.VALIDATION_REQUEST, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            self.ip_yp = self.access_coordinator.get_ip_yp_connected()
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "CONNECTION_DEAMON_INFO", LogType.VALIDATION_REQUEST, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            try:
                log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Searching for the yellow_page ...", LogType.CONNECTION_YP, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
                uri_yp = locate_yellow_page(self.nameserver, self.ip_yp)
                self.server = Pyro4.Proxy(uri_yp)
                log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> The yellow_page is connected with the IP: {self.ip_yp}", LogType.END_CONNECTION_YP, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            except Exception as e:
                log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Error: {e}", LogType.ERROR, ComponentType.DAEMON, time=0, success=False, uuid_agent=id_entity)
                raise CustomException(ErrorTypes.yp_not_registered)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "VALIDATION_REQUEST", LogType.END_CONNECTION_YP, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            if not is_valid_request_data(request):
                log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Invalid request data", LogType.END_VALIDATION_REQUEST, ComponentType.DAEMON, time=0, success=False, uuid_agent=id_entity)
                log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Request Invalid", LogType.END_REQUEST, ComponentType.DAEMON, time=0, success=False, uuid_agent=id_entity)
                raise CustomException(ErrorTypes.invalid_request)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "CONNECTION_YP", LogType.END_VALIDATION_REQUEST, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Request data is valid and Yellow Page is connected", LogType.END_VALIDATION_REQUEST, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Checking IP status", LogType.END_VALIDATION_ACL, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            ip_entity = conn.sock.getpeername()[0]
            status_ip = self.access_coordinator.check_ip_status(ip_entity, id_entity)
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> The IP {ip_entity} is in the {status_ip.status_ip} list", LogType.END_VALIDATION_ACL, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "END_VALIDATION_REQUEST", LogType.END_VALIDATION_ACL, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            if status_ip.status_ip == NameListSecurity.blacklist:
                log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> The IP {ip_entity} is in the blacklist", LogType.END_REQUEST, ComponentType.DAEMON, time=0, success=False, uuid_agent=id_entity)
                raise CustomException(ErrorTypes.ip_blocked)
            elif status_ip.status_ip != NameListSecurity.whitelist and status_ip.status_ip != NameListSecurity.blacklist:
                start_time = time.perf_counter()
                log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> The IP {ip_entity} is not in the ACL. Verifying if the request has the OTP code.", LogType.VALIDATION_TOTP_CODE, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            shared_key = self.get_hash_key(request, shared_key_agent, ip_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "END_VALIDATION_ACL", LogType.VALIDATION_TOTP_CODE, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Decrypting data ... {request}", LogType.DECRYPTION, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            data_decrypted = decrypt_data(request, shared_key)
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Data decrypted: {data_decrypted}", LogType.END_DECRYPTION, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "VALIDATION_TOTP_CODE", LogType.END_DECRYPTION, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            is_white = status_ip.status_ip == NameListSecurity.whitelist
            code_otp = data_decrypted.get("code_otp", None)
            if not is_white:
                if code_otp is None or code_otp == "":
                    start_time = time.perf_counter()
                    log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> TOTP is required", LogType.END_VALIDATION_TOTP_CODE, ComponentType.DAEMON, time=0, success=False ,uuid_agent=id_entity)
                    log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Request Invalid", LogType.END_REQUEST, ComponentType.DAEMON, time=0, success=False)
                    raise CustomException(ErrorTypes.otp_required)
                self.access_coordinator.authenticate(ip_entity, code_otp)
                log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> IP authenticated. TOTP Verified", LogType.END_VALIDATION_TOTP_CODE, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "DECRYPTION", LogType.END_VALIDATION_TOTP_CODE, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Validation completed successfully", LogType.END_VALIDATION_ACL, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "VALIDATION_ACL", LogType.END_VALIDATION_ACL, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            data = {
                "data_cifrated_yp": data_decrypted["data_cifrated_yp"],
                "code_totp": code_otp,
                "shared_key": shared_key_agent,
            }

            start_time = time.perf_counter()
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Encrypting data ...", LogType.ENCRYPTION, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            iv, data_cifrated = encrypt_data(self.access_coordinator.shared_key_yp, data)
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Data encrypted {data_cifrated}", LogType.END_ENCRYPTION, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "END_VALIDATION_TOTP_CODE", LogType.END_ENCRYPTION, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Sending data to the yellow_page ...", LogType.PREREGISTRATION, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            self.server.request_register({
                "id": id_entity,
                "ip_entity": ip_entity,
                "iv": iv,
                "data": data_cifrated
            })
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Key pairs generated successfully by the yellow_page", LogType.END_PREREGISTRATION, ComponentType.DAEMON, time=0, uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "END_ENCRYPTION", LogType.END_PREREGISTRATION, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            start_time = time.perf_counter()
            self.access_coordinator.server = self.server
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Redirecting to the GatewayManager ...", LogType.END_REQUEST, ComponentType.DAEMON, time=0,uuid_agent=id_entity)
            end_time = time.perf_counter()
            log_execution_time_with_message(self.access_coordinator.management_logs, "END_PREREGISTRATION", LogType.END_REQUEST, ComponentType.DAEMON, start_time, end_time, uuid_agent=id_entity)

            return "Hello"
        except CustomException as e:
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Error: {e}", LogType.ERROR, ComponentType.DAEMON, time=0, success=False, uuid_agent=id_entity)
            raise CustomException(e.error_type)
        except Exception as e:
            log_execution_time(self.access_coordinator.management_logs, f"Daemon -> {id_entity} -> Error: {e}", LogType.ERROR, ComponentType.DAEMON, time=0, success=False, uuid_agent=id_entity)
            raise CustomException(ErrorTypes.error_unknown)
