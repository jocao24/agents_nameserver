from typing import NamedTuple, Optional, Any

from src.utils.name_list_security import NameListSecurity


class ResponseType(NamedTuple):
    success: bool
    message: str
    status_ip: Optional[NameListSecurity]
    data: Optional[Any]
