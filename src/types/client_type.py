from typing_extensions import TypedDict, NotRequired


class ClientType(TypedDict):
    id: str
    name: str
    description: str
    local_ip: str
    ip_name_server: NotRequired[str]
