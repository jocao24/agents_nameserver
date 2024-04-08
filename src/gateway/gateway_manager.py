from threading import Event
from typing import TypedDict
import threading
import Pyro4
from src.menus.menu_nameserver import MenuNameServer
from src.menus.yellow_page_integration import YellowPageIntegration
from src.manage_logs.manage_logs import log_message
from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils.pyro_config import configure_pyro

configure_pyro()


class GatewayManagerType(TypedDict):
    nameserver: Pyro4.Proxy
    yp_event: Event
    finally_name_server: Event
    deamon: Pyro4.Daemon
    access_coordinator: AccessCoordinator
    menu: MenuNameServer


class GatewayManager:
    def __init__(self, params: GatewayManagerType):
        self.yp_event = params["yp_event"]
        self.nameserver = params["nameserver"]
        self.access_coordinator = params["access_coordinator"]
        self.server = None
        self.menu = params["menu"]
        self.yp_integration = YellowPageIntegration(self.yp_event, params['finally_name_server'], self.nameserver, self.access_coordinator)
        self.check_server_thread = threading.Thread(target=self.yp_integration.config_ip, daemon=True)
        self.check_server_thread.start()

    def get_ip_entinty(self):
        return Pyro4.current_context.client_sock_addr[0]

    def execute_operation(self, skill, num1, num2):
        log_message(f"Operation {skill} with numbers {num1} and {num2} requested.")
        return self.server.execute_operation(skill, num1, num2)

    @Pyro4.expose
    def register(self, id_agent: str):
        data = self.access_coordinator.server.get_access_data_for_register(id_agent)
        return data
