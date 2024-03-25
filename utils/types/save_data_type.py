from typing_extensions import TypedDict, NotRequired


class SaveDataType(TypedDict):
    blacklist: set
    whitelist: set
    yellow_page_list: set
