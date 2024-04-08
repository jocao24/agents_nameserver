from enum import Enum, auto


class NameListSecurity(Enum):
    blacklist = 'blacklist'
    whitelist = 'whitelist'
    yellow_page_list = 'yellow_page_list'
