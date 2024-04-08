from typing_extensions import TypedDict, NotRequired


class ClientNSType(TypedDict):
    id: str
    name: str
    description: str
    code_otp: NotRequired[str]
    ip_client: NotRequired[str]
