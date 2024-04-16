from src.manage_logs.manage_logs import ManagementLogs
from src.security.access_coordinator.data_management import DataManagement
from src.types.response_type import ResponseType
from src.utils.name_list_security import NameListSecurity


class IPManager:
    def __init__(self, management_logs: ManagementLogs):
        self.management_logs = management_logs
        self.access_list_keeper = DataManagement(management_logs)
        self.data_to_save = {
            'blacklist': set(),
            'whitelist': set(),
            'yellow_page_list': set(),
            'logs': '',
            'ultimate_shared_key': '',
            'ultimate_shared_key_agent': ''
        }
        self.refresh_lists()
        self.management_logs.log_message('IPManager -> IPManager initialized')

    def refresh_lists(self):
        self.data_to_save = self.access_list_keeper.load()

    def __move_ip_between_lists(self, ip, from_list: NameListSecurity, to_list: NameListSecurity):
        self.management_logs.log_message(f"IPManager -> Moving IP {ip} from {from_list.value} to {to_list.value}")
        from_list_name = from_list.value
        to_list_name = to_list.value
        if ip in self.data_to_save[to_list_name]:
            self.management_logs.log_message(f"IPManager -> The IP {ip} is already in the {to_list_name}.")
            return ResponseType(
                success=False,
                message=f"The IP {ip} is already in the {to_list_name}.",
                data=None,
                status_ip=None
            )
        if ip in self.data_to_save[from_list_name]:
            self.management_logs.log_message(f"IPManager -> The IP {ip} is not in the {from_list_name}.")
            self.data_to_save[from_list_name].remove(ip)
        self.management_logs.log_message(f"IPManager -> The IP {ip} has been moved from the {from_list_name} to the {to_list_name}.")
        self.data_to_save[to_list_name].add(ip)
        self.management_logs.log_message("IPManager -> Saving the data.")
        self.access_list_keeper.save(self.data_to_save)
        self.management_logs.log_message("IPManager -> Data saved successfully.")
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been moved from the {from_list_name} to the {to_list_name}.",
            data=self.data_to_save[to_list_name],
            status_ip=to_list
        )

    def add_ip_to_list(self, ip, list_type: NameListSecurity):
        self.management_logs.log_message(f"IPManager -> Adding IP {ip} to the {list_type.value}")
        list_name = list_type.value
        if list_type in [NameListSecurity.blacklist, NameListSecurity.whitelist]:
            opposite_list = NameListSecurity.blacklist
            if list_type == NameListSecurity.blacklist:
                opposite_list = NameListSecurity.whitelist
            opposite_list = opposite_list.value
            if ip in self.data_to_save[list_name]:
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} is already in the {list_name}.",
                    data=None,
                    status_ip=list_type
                )
            if ip in self.data_to_save[opposite_list]:
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} cannot be added to the {list_name} because it is in the {opposite_list}.",
                    data=None,
                    status_ip=opposite_list
                )
        else:
            if ip in self.data_to_save[list_name]:
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} is already in the {list_name}.",
                    data=None,
                    status_ip=list_type
                )
        self.management_logs.log_message(f"IPManager -> The IP {ip} has been added to the {list_name}.")
        self.data_to_save[list_name].add(ip)
        self.management_logs.log_message("IPManager -> Saving the data.")
        self.access_list_keeper.save(self.data_to_save)
        self.management_logs.log_message("IPManager -> Data saved successfully.")
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been added to the {list_name}.",
            data=self.data_to_save[list_name],
            status_ip=list_type
        )

    def remove_ip_from_list(self, ip, list_type: NameListSecurity, move_to_list: NameListSecurity = None):
        self.management_logs.log_message(f"IPManager -> Removing IP {ip} from the {list_type.value}")
        if move_to_list:
            return self.__move_ip_between_lists(ip, list_type, move_to_list)
        list_name = list_type.value

        if ip not in self.data_to_save[list_name]:
            return ResponseType(False, f"The IP {ip} is not in the {list_name}.", None, list_type)

        self.management_logs.log_message(f"IPManager -> The IP {ip} has been removed from the {list_name}.")
        self.data_to_save[list_name].remove(ip)
        self.management_logs.log_message("IPManager -> Saving the data.")
        self.access_list_keeper.save(self.data_to_save)
        self.management_logs.log_message("IPManager -> Data saved successfully.")
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been removed from the {list_name}.",
            data=self.data_to_save[list_name],
            status_ip=list_type
        )

    def check_ip_status(self, ip):
        self.management_logs.log_message(f"IPManager -> Checking the status of the IP {ip}")
        is_blacklisted = ip in self.data_to_save['blacklist']
        is_whitelisted = ip in self.data_to_save['whitelist']
        if is_blacklisted:
            self.management_logs.log_message(f"IPManager -> The IP {ip} is blacklisted.")
            status_messages = f"The IP {ip} is blacklisted."
            return ResponseType(True, status_messages, NameListSecurity.blacklist, None)
        if is_whitelisted:
            self.management_logs.log_message(f"IPManager -> The IP {ip} is whitelisted.")
            status_messages = f"The IP {ip} is whitelisted."
            return ResponseType(True, status_messages, NameListSecurity.whitelist, None)
        if not is_blacklisted and not is_whitelisted:
            self.management_logs.log_message(f"IPManager -> The IP {ip} has no specific access status.")
            status_messages = f"The IP {ip} has no specific access status."
            return ResponseType(False, status_messages, None, None)

    def delete_all_lists(self):
        self.management_logs.log_message("IPManager -> Deleting all lists.")
        self.data_to_save = {
            'blacklist': set(),
            'whitelist': set(),
            'yellow_page_list': set(),
            'logs': '',
            'ultimate_shared_key': '',
            'ultimate_shared_key_agent': ''
        }
        self.management_logs.log_message("IPManager -> Saving the data.")
        self.access_list_keeper.save(self.data_to_save)
        self.management_logs.log_message("IPManager -> Data saved successfully.")
        return ResponseType(
            success=True,
            message="All lists have been cleared.",
            data=None,
            status_ip=None
        )

    def get_ips_in_list(self, list_type: NameListSecurity):
        self.management_logs.log_message(f"IPManager -> Getting IPs in the {list_type.value}")
        list_name = list_type.value
        return ResponseType(
            success=True,
            message=f"IPs in the {list_name}.",
            data=self.data_to_save[list_name],
            status_ip=list_type
        )
