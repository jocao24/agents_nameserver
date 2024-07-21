from threading import Event
from typing import TypedDict
import threading
import Pyro4
from src.menus.menu_nameserver import MenuNameServer
from src.menus.yellow_page_integration import YellowPageIntegration
from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils.pyro_config import configure_pyro
from src.manage_logs.manage_logs_v_2 import ManagementLogs
from src.manage_logs.manage_logs_v_2 import LogType, ComponentType

configure_pyro()


class GatewayManagerType(TypedDict):
    nameserver: Pyro4.Proxy
    yp_event: Event
    finally_name_server: Event
    daemon: Pyro4.Daemon
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
        self.access_coordinator.management_logs.log_message(ComponentType.GATEWAY_MANAGER, "GatewayManager started", LogType.START_SESSION, True)

    @Pyro4.expose
    def register(self, id_agent: str):
        self.access_coordinator.management_logs.log_message(ComponentType.GATEWAY_MANAGER, f"{id_agent} -> Registering agent", LogType.REGISTRATION, True)
        data = self.access_coordinator.server.get_access_data_for_register(id_agent)
        self.access_coordinator.management_logs.log_message(ComponentType.GATEWAY_MANAGER, f"{id_agent} -> Registered agent", LogType.REGISTRATION, True)
        return data
