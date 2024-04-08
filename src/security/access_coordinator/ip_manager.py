from src.security.access_coordinator.access_list_keeper import AccessListKeeper
from src.types.response_type import ResponseType
from src.utils.name_list_security import NameListSecurity


class IPManager:
    def __init__(self, password):
        self.access_list_keeper = AccessListKeeper(password)
        self.ip_lists = {'blacklist': set(), 'whitelist': set(), 'yellow_page_list': set()}
        self.refresh_lists()

    def refresh_lists(self):
        self.ip_lists = self.access_list_keeper.load()

    def __move_ip_between_lists(self, ip, from_list: NameListSecurity, to_list: NameListSecurity):
        from_list_name = from_list.value
        to_list_name = to_list.value
        if ip in self.ip_lists[to_list_name]:
            return ResponseType(
                success=False,
                message=f"The IP {ip} is already in the {to_list_name}.",
                data=None,
                status_ip=None
            )
        if ip in self.ip_lists[from_list_name]:
            self.ip_lists[from_list_name].remove(ip)
        self.ip_lists[to_list_name].add(ip)
        self.access_list_keeper.save(self.ip_lists)
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been moved from the {from_list_name} to the {to_list_name}.",
            data=self.ip_lists[to_list_name],
            status_ip=to_list
        )

    def add_ip_to_list(self, ip, list_type: NameListSecurity):
        list_name = list_type.value
        if list_type in [NameListSecurity.blacklist, NameListSecurity.whitelist]:
            opposite_list = NameListSecurity.blacklist
            if list_type == NameListSecurity.blacklist:
                opposite_list = NameListSecurity.whitelist
            opposite_list = opposite_list.value
            if ip in self.ip_lists[list_name]:
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} is already in the {list_name}.",
                    data=None,
                    status_ip=list_type
                )
            if ip in self.ip_lists[opposite_list]:
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} cannot be added to the {list_name} because it is in the {opposite_list}.",
                    data=None,
                    status_ip=opposite_list
                )
        else:
            if ip in self.ip_lists[list_name]:
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} is already in the {list_name}.",
                    data=None,
                    status_ip=list_type
                )
        self.ip_lists[list_name].add(ip)
        self.access_list_keeper.save(self.ip_lists)
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been added to the {list_name}.",
            data=self.ip_lists[list_name],
            status_ip=list_type
        )

    def remove_ip_from_list(self, ip, list_type: NameListSecurity, move_to_list: NameListSecurity = None):
        if move_to_list:
            return self.__move_ip_between_lists(ip, list_type, move_to_list)
        list_name = list_type.value

        if ip not in self.ip_lists[list_name]:
            return ResponseType(False, f"The IP {ip} is not in the {list_name}.", None, list_type)

        self.ip_lists[list_name].remove(ip)
        self.access_list_keeper.save(self.ip_lists)
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been removed from the {list_name}.",
            data=self.ip_lists[list_name],
            status_ip=list_type
        )

    def check_ip_status(self, ip):
        is_blacklisted = ip in self.ip_lists['blacklist']
        is_whitelisted = ip in self.ip_lists['whitelist']
        if is_blacklisted:
            status_messages = f"The IP {ip} is blacklisted."
            return ResponseType(True, status_messages, NameListSecurity.blacklist, None)
        if is_whitelisted:
            status_messages = f"The IP {ip} is whitelisted."
            return ResponseType(True, status_messages, NameListSecurity.whitelist, None)
        if not is_blacklisted and not is_whitelisted:
            status_messages = f"The IP {ip} has no specific access status."
            return ResponseType(False, status_messages, None, None)

    def delete_all_lists(self):
        self.ip_lists = {'blacklist': set(), 'whitelist': set(), 'yellow_page_list': set()}
        self.access_list_keeper.save(self.ip_lists)
        return ResponseType(
            success=True,
            message="All lists have been cleared.",
            data=None,
            status_ip=None
        )

    def get_ips_in_list(self, list_type: NameListSecurity):
        list_name = list_type.value
        return ResponseType(
            success=True,
            message=f"IPs in the {list_name}.",
            data=self.ip_lists[list_name],
            status_ip=list_type
        )
