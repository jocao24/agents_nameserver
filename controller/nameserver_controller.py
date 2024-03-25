import Pyro4
from Pyro4 import Proxy

from utils.types.client_nameserver_type import ClientNSType
from utils.types.agent_nameserver_type import AgentNSType
from utils.custom_exception import ErrorTypes, CustomException
from utils.types_entities import TypesEntities as Ent


@Pyro4.expose
class NameServerController:

    @Pyro4.expose
    def ping(self, data):
        pass



