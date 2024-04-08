from typing_extensions import TypedDict


class RequestDataType(TypedDict):
    iv: str
    data: str
    id: str
