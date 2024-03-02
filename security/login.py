import uuid
import Pyro4
from utils.types.agent_nameserver_type import AgentNSType
from utils.types.client_nameserver_type import ClientNSType
from utils.types_entities import TypesEntities
from utils.errors import ErrorTypes
from utils.custom_exception import CustomException
from utils.get_date import print_current_time


class Login:
    def __init__(self, type_ent: TypesEntities, data_ent: ClientNSType or AgentNSType, nameserver, gateway):
        self.type_entity = type_ent
        self.data_entity = data_ent
        self.gateway = gateway
        self.attempts = 0
        self.validate_parameters()

        if not self.gateway:
            self.connect_nameserver(nameserver)

    def validate_parameters(self):
        if not self.type_entity:
            raise CustomException(ErrorTypes.type_entity_required)
        try:
            uuid.UUID(self.data_entity['id'])
        except ValueError:
            raise CustomException(ErrorTypes.invalid_uuid)

    def connect_nameserver(self, nameserver):
        try:
            if self.type_entity == TypesEntities.agent:
                nameserver.register(self.data_entity['name'], self.data_entity['uri'])
            if not self.gateway:
                self.gateway = Pyro4.Proxy(self.data_entity['uri'])
                print("Gateway localizado")
        except TypeError as E:
            print(E)
            raise CustomException(ErrorTypes.gateway_not_found)

    def authenticate(self):
        response = self.gateway.register_entity(self.type_entity, self.data_entity)
        if response is True:
            print("Successfully authenticated to the: ", print_current_time())
            gateway_uri = str(self.gateway)
            return gateway_uri
        else:
            print("Error in the authentication to the: ", print_current_time())
            error_code = str(response).split(":")[0].strip()
            if error_code == ErrorTypes.ip_blocked.value[0]:
                print(response)
                exit(1)
            else:
                raise CustomException(ErrorTypes(response))

