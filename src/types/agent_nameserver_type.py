from typing_extensions import TypedDict, NotRequired, Any


class AgentNSType(TypedDict):
    id: str
    name: str
    description: str
    code_otp: NotRequired[str]
    ip_agent: NotRequired[str]
    skills: list[str]
    uri: Any
