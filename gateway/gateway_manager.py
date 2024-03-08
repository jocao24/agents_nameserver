import sys
import threading
import time
import Pyro4
from gateway.class_for_gateway.manage_data_gateway import ManageDataNameServer
from manage_logs.manage_logs import log_message, get_end_session_log
from security.authenticate import AuthenticationManager
from utils.errors import ErrorTypes
from utils.types.agent_nameserver_type import AgentNSType
from utils.types.client_nameserver_type import (ClientNSType)
from utils.get_ip import get_ip
from utils.types_entities import TypesEntities
from utils.custom_exception import CustomException
from utils.pyro_config import configure_pyro
from utils.validate_ip import validate_ip

configure_pyro()
local_ip = get_ip()
port_nameserver = 9090


class GatewayManager:
    def __init__(self, event, finally_name_server):
        self.event = event
        self.finally_name_server = finally_name_server
        self.nameserver = Pyro4.locateNS(host=local_ip, port=port_nameserver)
        self.server_uri = None
        self.server = None
        self.check_server_thread = threading.Thread(target=self.check_server)
        self.check_server_thread.start()
        self.security_manager = AuthenticationManager()

    def request_ip(self) -> str:
        request_ip = True
        while request_ip:
            ip_yp = input("Enter the IP of the yellow_page. If it is the same as the NameServer, press enter: ")
            if ip_yp:
                is_valid_ip = validate_ip(ip_yp)
                if not is_valid_ip:
                    print("The IP entered is not valid. Please enter a valid IP.")
                    log_message("The IP entered is not valid. Please enter a valid IP.")
                else:
                    request_ip = False
            else:
                ip_yp = get_ip()
                request_ip = False
            log_message(f"The IP of the yellow_page is: {ip_yp}")
        return ip_yp

    def check_server(self):
        time.sleep(1)
        ip_yp = None
        while True:
            is_valid_ip = False
            opt_select = input("Do you want to use the yellow_page IP saved in the configuration file? (y/n): ")
            if opt_select.lower() == 'y':
                ip_yp = ManageDataNameServer().get_config()
                if ip_yp:
                    is_valid_ip = validate_ip(ip_yp)
                if not is_valid_ip or not ip_yp:
                    message = "The IP of the yp saved in the configuration file is not valid. Please enter a valid IP."
                    print(message)
                    log_message(message)
                    ip_yp = self.request_ip()
                break
            elif opt_select.lower() == 'n':
                ip_yp = self.request_ip()
                break
            else:
                message = "Invalid option. Please enter a valid option."
                print(message)
                log_message(message)

        if ip_yp:
            ManageDataNameServer().save_config(ip_yp)
            message = f"Wating for the yellow_page to be registered at {ip_yp}..."
            print(message)
            log_message(message)
            while self.server_uri is None:
                try:
                    name_yellow_page = 'yellow_page@' + ip_yp
                    self.server_uri = self.nameserver.lookup(name_yellow_page)
                    if self.server_uri:
                        self.server = Pyro4.Proxy(self.server_uri)
                        ip = self.server_uri.location
                        # print("The yellow_page has been registered! Your ip is:", ip)
                        message = f"The yellow_page has been registered! Your ip is: {ip}"
                        log_message(message)
                        print(message)
                        self.event.set()
                        time.sleep(1)
                    else:
                        time.sleep(1)

                except Pyro4.errors.NamingError:
                    time.sleep(1)

        self.manage_gateway()

    def get_ip_entinty(self):
        return Pyro4.current_context.client_sock_addr[0]

    @Pyro4.expose
    def register_entity(self, type_entity: TypesEntities, data_entity: ClientNSType or AgentNSType):
        if type_entity == TypesEntities.client:
            return self.register_client(data_entity)
        elif type_entity == TypesEntities.agent:
            return self.register_agent(data_entity)

    @Pyro4.expose
    def register_client(self, client_data: ClientNSType):
        ip_entity = self.get_ip_entinty()
        try:
            code_otp = client_data.get("code_otp", None)
            log_message(f"Client registration request {client_data['name']}.")
            is_authenticated = self.security_manager.authenticate(ip_entity, client_data["name"], "client", code_otp)
            log_message(f"Client registration request {client_data['name']} was {is_authenticated}.")
            if is_authenticated is True:
                return True
            else:
                message = "Warning: The client could not be registered."
                log_message(message)
                raise ValueError(message)
        except CustomException as e:
            log_message(f"Error: {e.error_type.message}")
            return {"error": e.error_type.code, "message": e.error_type.message}

    @Pyro4.expose
    def register_agent(self, agent_data: AgentNSType):
        ip_entity = self.get_ip_entinty()
        try:
            code_otp = agent_data.get("code_otp", None)
            log_message(f"Agent registration request {agent_data['name']}.")
            is_authenticated = self.security_manager.authenticate(ip_entity, agent_data["name"], "agent", code_otp)
            log_message(f"Agent registration request {agent_data['name']} was {is_authenticated}.")
            if is_authenticated is True:
                self.server.register_agent({
                    "name": agent_data["name"],
                    "description": agent_data["description"],
                    "id": agent_data["id"],
                    "skills": agent_data["skills"],
                    "ip_agent": ip_entity
                })
                return True
            else:
                message = "Warning: The agent could not be registered."
                log_message(message)
                raise ValueError(message)
        except CustomException as e:
            # if e.error_type.code == ErrorTypes.ip_blocked.code:
                # en lugar de enviar una ip se envian las ip que aparecen en la lista negra
                # self.server.remove_agent(ip_entity)
            return {"error": e.error_type.code, "message": e.error_type.message}

    @Pyro4.expose
    def execute_operation(self, skill, num1, num2):
        log_message(f"Operation {skill} with numbers {num1} and {num2} requested.")
        if not self.server:
            message = f"The yellow_page is not registered or is not active."
            log_message(message)
            raise Pyro4.errors.CommunicationError("The yellow_page is not registered or is not active.")
        return self.server.execute_operation(skill, num1, num2)

    @Pyro4.expose
    def get_skills(self):
        if not self.server:
            message = f"The yellow_page is not registered or is not active."
            log_message(message)
            raise Pyro4.errors.CommunicationError("The yellow_page is not registered or is not active.")
        return self.server.get_skills()

    def manage_gateway(self):
        while True:
            logs = get_end_session_log()
            print("1. View logs")
            print("2. Add whitelist")
            print("3. Add blacklist")
            print("4. View whitelist")
            print("5. View blacklist")
            print("6. Remove whitelist")
            print("7. Remove blacklist")
            print("8. Exit")
            option = input("Enter the number of the option you want to execute: ")
            if option.isdigit():
                option = int(option)
                if option == 1:
                    print("===================================================================")
                    logs = get_end_session_log()
                    print(logs)
                    print("====================================================================")
                elif option == 2:
                    ip = input("Enter the IP you want to add to the whitelist: ")
                    is_valid_ip = validate_ip(ip)
                    if is_valid_ip:
                        messages = self.security_manager.add_whhite_list(ip)
                        for message in messages:
                            print(message)
                    else:
                        print("The IP entered is not valid. Please enter a valid IP.")
                elif option == 3:
                    ip = input("Enter the IP you want to add to the blacklist: ")
                    is_valid_ip = validate_ip(ip)
                    if is_valid_ip:
                        messages = self.security_manager.add_blacklist(ip)
                        for message in messages:
                            print(message)
                    else:
                        print("The IP entered is not valid. Please enter a valid IP.")

                elif option == 4:
                    whitelist = self.security_manager.get_whitelist()
                    i = 1
                    print("====================================================================")
                    if len(whitelist):
                        for ip in whitelist:
                            print(f"{i}. {ip}")
                            i += 1
                    else:
                        print("The whitelist is empty.")
                    print("====================================================================")

                elif option == 5:
                    blacklist = self.security_manager.get_blacklist()
                    i = 1
                    print("====================================================================")
                    if len(blacklist):
                        for ip in blacklist:
                            print(f"{i}. {ip}")
                        i += 1
                    else:
                        print("The blacklist is empty.")
                    print("====================================================================")

                elif option == 6:
                    whitelist = self.security_manager.get_whitelist()
                    i = 1
                    print("====================================================================")
                    for ip in whitelist:
                        print(f"{i}. {ip}")
                        i += 1

                    if len(whitelist):
                        ip = input("Enter the number of the IP you want to remove from the whitelist: ")
                        if ip.isdigit():
                            ip = int(ip)
                            if 0 < ip <= len(whitelist):
                                ip = list(whitelist)[ip - 1]
                                opt_select = input("Do you want to add it to the blacklist? (y/n): ")
                                messages = self.security_manager.remove_whitelist(ip)
                                if opt_select.lower() != 'n' and opt_select.lower() != 'y':
                                    print("Invalid option. Please enter a valid option.")
                                else:
                                    if opt_select.lower() == 'y':
                                        messages.append(self.security_manager.add_blacklist(ip))
                                    for message in messages:
                                        print(message)

                            else:
                                print("Invalid number. Please enter a valid number.")
                        else:
                            print("Invalid number. Please enter a valid number.")
                    else:
                        print("The whitelist is empty.")
                    print("====================================================================")

                elif option == 7:
                    # Show blacklist
                    blacklist = self.security_manager.get_blacklist()
                    i = 1
                    print("====================================================================")
                    for ip in blacklist:
                        print(f"{i}. {ip}")
                        i += 1
                    if len(blacklist):
                        ip = input("Enter the number of the IP you want to remove from the blacklist: ")
                        if ip.isdigit():
                            ip = int(ip)
                            if 0 < ip <= len(blacklist):
                                ip = list(blacklist)[ip - 1]
                                opt_select = input("Do you want to add it to the whitelist? (y/n): ")
                                if opt_select.lower() != 'n' and opt_select.lower() != 'y':
                                    print("Invalid option. Please enter a valid option.")
                                else:
                                    messages = self.security_manager.remove_blacklist(ip)
                                    if opt_select.lower() == 'y':
                                        messages.append(self.security_manager.add_whhite_list(ip))
                                    for message in messages:
                                        print(message)
                            else:
                                print("Invalid number. Please enter a valid number.")
                        else:
                            print("Invalid number. Please enter a valid number.")

                    else:
                        print("The blacklist is empty.")
                    print("====================================================================")

                elif option == 8:
                    self.finally_name_server.set()
                    break
                else:
                    print("Invalid option. Please enter a valid option.")
            else:
                print("Invalid option. Please enter a valid option.")
