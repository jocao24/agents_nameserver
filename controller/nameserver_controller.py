import Pyro4
from utils.types.client_nameserver_type import ClientNSType
from utils.types.agent_nameserver_type import AgentNSType
from security.login import Login
from utils.custom_exception import ErrorTypes
from utils.types_entities import TypesEntities as Ent


@Pyro4.expose
class NameServerController:

    def __init__(self, nameserver, gateway, gateway_uri=None):
        self.nameserver = nameserver
        self.gateway = gateway
        self.gateway_uri = gateway_uri

    @Pyro4.expose
    def authenticate_client_in_gateway(self, data_entity: ClientNSType):
        try:
            gateway_instance = Login(Ent.client, data_entity, self.nameserver, self.gateway)
            gateway_instance.authenticate()
            result = {
                "is_authenticated": True,
                "gateway_uri": self.gateway_uri
            }
            return result
        except Exception as e:
            error_type = self.determine_error_type(e)
            print("Authentication error:", error_type)
            return {
                "error": error_type.code,
                "message": error_type.message.lower()
            }

    @Pyro4.expose
    def authenticate_agent_in_gateway(self, data_entity: AgentNSType):
        try:
            gateway_instance = Login(Ent.agent, data_entity, self.nameserver, self.gateway)
            gateway_instance.authenticate()
            result = {
                "is_authenticated": True,
                "gateway_uri": self.gateway_uri
            }
            return result
        except Exception as e:
            error_type = self.determine_error_type(e)
            print("Authentication error:", error_type)
            return {
                "error": error_type.code,
                "message": error_type.message.lower()
            }

    def determine_error_type(self, exception):
        message = str(exception).lower()
        for error_type in ErrorTypes:
            if error_type.value[1].lower() in message:
                return error_type
        return ErrorTypes.error_unknown
