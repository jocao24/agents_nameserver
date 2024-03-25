from threading import Event
from typing import TypedDict
import threading
import Pyro4

from gateway.class_for_gateway.menu import Menu
from gateway.class_for_gateway.yellow_page_integration import YellowPageIntegration
from manage_logs.manage_logs import log_message
from security.authenticate import AuthenticationManager
from utils.errors import ErrorTypes
from utils.types.agent_nameserver_type import AgentNSType
from utils.types.client_nameserver_type import (ClientNSType)
from utils.types_entities import TypesEntities
from utils.custom_exception import CustomException
from utils.pyro_config import configure_pyro

configure_pyro()


class GatewayManagerType(TypedDict):
    nameserver: Pyro4.Proxy
    yp_event: Event
    finally_name_server: Event
    deamon: Pyro4.Daemon
    auth_manager: AuthenticationManager
    menu: Menu


class GatewayManager:
    def __init__(self, params: GatewayManagerType):
        self.yp_event = params["yp_event"]
        self.nameserver = params["nameserver"]
        self.auth_manager = params["auth_manager"]
        self.server = None
        self.menu = params["menu"]
        self.yp_integration = YellowPageIntegration(self.yp_event, params['finally_name_server'], self.nameserver, self.auth_manager)
        self.check_server_thread = threading.Thread(target=self.yp_integration.config_ip, daemon=True)  # Hacer el hilo daemon
        self.check_server_thread.start()

    def register_entity(self, type_entity: TypesEntities, data_entity: ClientNSType or AgentNSType):
        if self.yp_integration.is_up_yellow_page():
            try:

                if type_entity == TypesEntities.client:
                    return self.register_client(data_entity)
                elif type_entity == TypesEntities.agent:
                    return self.register_agent(data_entity)
            except Pyro4.errors.CommunicationError:
                message = "The yellow_page is not registered or is not active."
                log_message(message)
                return {"error": ErrorTypes.yp_not_registered.code, "message": message}

    def get_ip_entinty(self):
        return Pyro4.current_context.client_sock_addr[0]

    def execute_operation(self, skill, num1, num2):
        log_message(f"Operation {skill} with numbers {num1} and {num2} requested.")
        return self.server.execute_operation(skill, num1, num2)


    @Pyro4.expose
    def register(self, id_agent: str):
        data = self.auth_manager.server.get_access_data_for_register(id_agent)
        return data
