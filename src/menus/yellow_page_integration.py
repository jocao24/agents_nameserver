from threading import Event
import time
import Pyro5.nameserver
import Pyro5.errors
import Pyro5.core
import Pyro5.api

from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils.errors import ErrorTypes
from src.utils.get_ip import get_ip
from src.utils.get_name_device import get_name_device
from src.utils.name_list_security import NameListSecurity
from src.utils.separators import show_separators, show_center_text_with_separators
from src.utils.validate_ip import validate_ip


class YellowPageIntegration:
    def __init__(self, yp_event: Event, finally_ns: Event, ns: Pyro5.nameserver.NameServer, access_coordinator: AccessCoordinator):
        self.yp_event = yp_event
        self.finally_name_server = finally_ns
        self.nameserver = ns
        self.server_uri = None
        self.server = None
        self.ip_yp = None
        self.access_coordinator = access_coordinator

    def _request_ip(self):
        self.access_coordinator.management_logs.log_message("YellowPageIntegration -> Requesting the IP of the yellow_page...")
        request_ip = True
        ip_yp = None
        while request_ip:
            print()
            ip_yp = input("Enter the IP of the yellow_page. If it is the same as the NameServer, press enter: ")
            if ip_yp:
                is_valid_ip = validate_ip(ip_yp)
                if not is_valid_ip:
                    print(ErrorTypes.invalid_ip.message)
                    self.access_coordinator.management_logs.log_message(f'YellowPageIntegration -> Error: {ErrorTypes.invalid_ip.message}')
                else:
                    request_ip = False
            else:
                ip_yp = get_ip()
                request_ip = False
            self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> The IP of the yellow_page is: {ip_yp}")
            response = self.access_coordinator.add_ip_to_list(ip_yp,  NameListSecurity.yellow_page_list)
            self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> Response: {response}")
        self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> The IP of the yellow_page is: {ip_yp}")
        return ip_yp

    def select_ip(self, ips: list[str]):
        self.access_coordinator.management_logs.log_message("YellowPageIntegration -> Selecting the yellow_page IP...")
        i = 1
        print("")
        print(show_center_text_with_separators("Yellow Page List"))
        for ip in ips:
            name_device = get_name_device(ip, self.access_coordinator.management_logs)
            if name_device:
                print(f"{i}. {ip} - {name_device} - Active")
                i += 1
            else:
                self.access_coordinator.remove_ip_from_list(ip, NameListSecurity.yellow_page_list)
        if i == 1:
            self.access_coordinator.management_logs.log_message("YellowPageIntegration -> There are no yellow_page IPs saved in the file.")
            return self._request_ip()
        else:
            self.access_coordinator.management_logs.log_message("YellowPageIntegration -> Selecting the yellow_page IP...")
            num_ip_sel = input("Enter the number of the yellow_page IP you want to use: ")
            if num_ip_sel.isdigit() and 0 < int(num_ip_sel) <= len(ips):
                print(show_center_text_with_separators(f"The IP {ips[int(num_ip_sel) - 1]} has been selected."))
                print(show_separators())
                self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> The IP {ips[int(num_ip_sel) - 1]} has been selected.")
                return ips[int(num_ip_sel) - 1]
            else:
                self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> Invalid option. The number must be between 1 and {len(ips)}.")
                print(show_separators())
                return None

    def __select_or_request_ip(self):
        self.access_coordinator.management_logs.log_message("YellowPageIntegration -> Selecting or requesting the yellow_page IP...")
        ips = self.access_coordinator.get_ips_in_list(NameListSecurity.yellow_page_list).data
        self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> IPs in the yellow_page list: {ips}")
        print(show_separators())
        print(show_center_text_with_separators("Yellow Page Configuration"))
        if ips and len(ips) > 0:
            self.access_coordinator.management_logs.log_message("YellowPageIntegration -> Selecting the yellow_page IP...")
            opt_select = input("Do you want to use the yellow_page IP saved in the file? (y/n): -> default y ")
            if opt_select.lower() == 'y' or opt_select == '':
                self.access_coordinator.management_logs.log_message("YellowPageIntegration -> Selecting the yellow_page IP from the list...")
                ip = self.select_ip(list(ips))
                return ip
            elif opt_select.lower() == 'n':
                self.access_coordinator.management_logs.log_message("YellowPageIntegration -> Requesting the yellow_page IP...")
                return self._request_ip()
            else:
                self.access_coordinator.management_logs.log_message("YellowPageIntegration -> Invalid option. The option must be 'y' or 'n'.")
        else:
            return self._request_ip()

    def __verify_yellow_page(self, ip_yp):
        message = f"Wating for the yellow_page to be registered in the device {get_name_device(ip_yp, self.access_coordinator.management_logs)}..."
        print(message)
        return self.check_server(message, 1, 50)

    def config_ip(self):
        time.sleep(1)
        self.ip_yp = self.__select_or_request_ip()
        if self.ip_yp:
            self.access_coordinator.add_ip_to_list(self.ip_yp, NameListSecurity.yellow_page_list)
            if self.__verify_yellow_page(self.ip_yp):
                if self.access_coordinator.validate_shared_key(self.ip_yp):
                    print(show_separators())
                    print(show_center_text_with_separators("The yellow_page has been correctly configured"))
                    print("\n")
                    self.yp_event.set()
                else:
                    self.finally_name_server.set()
            else:
                print(show_separators())
                print(show_center_text_with_separators("The yellow_page is not registered or is not active."))
                print("\n")
                self.finally_name_server.set()
        else:
            print("IP configuration was not completed.")

    def check_server(self, message: str, time_sleep: int = 1, max_attempts: int = 10):
        self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> {message}")
        found_yellow_page = False
        self.server_uri = None
        while self.server_uri is None and max_attempts > 0:
            self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> Attempt {11 - max_attempts} to connect to the yellow_page...")
            try:
                name_yellow_page = 'yellow_page' + self.ip_yp
                self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> Looking for the yellow_page with the name: {name_yellow_page}")
                self.server = Pyro5.api.Proxy(f'PYROMETA:{name_yellow_page}')
                ping = self.server.ping()
                if ping == "pong":
                    self.server_uri = self.server._pyroUri
                    print(f"URI: {self.server_uri}")
                    self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> The yellow_page has been found with the URI: {self.server_uri}")
                    self.access_coordinator.set_ip_yp_connected(self.ip_yp, self.server)
                    message = (f"The device {get_name_device(self.ip_yp, self.access_coordinator.management_logs)} has been correctly configured as "
                               f"yellow_page.")
                    self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> {message}")
                    print(message)
                    found_yellow_page = True

            except Pyro5.errors.NamingError as e:
                self.access_coordinator.management_logs.log_message(
                    f"YellowPageIntegration -> Error: {ErrorTypes.yellow_page_not_found.message}")
            except Exception as e:
                self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> Error: {e}")
            finally:
                max_attempts -= 1
                time.sleep(time_sleep)

        return found_yellow_page

    def is_up_yellow_page(self):
        message = f"Wating for the yellow_page to be registered at {self.ip_yp}..."
        found_yp = self.check_server(message, 1, 10)
        if not found_yp:
            message = "The yellow_page is not registered or is not active."
            self.access_coordinator.management_logs.log_message(f"YellowPageIntegration -> {message}")
            raise Pyro5.errors.CommunicationError(message)
        return found_yp
