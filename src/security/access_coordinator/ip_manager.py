import time
from src.manage_logs.manage_logs_v_2 import ComponentType, LogType, ManagementLogs
from src.security.access_coordinator.data_management import DataManagement
from src.types.response_type import ResponseType
from src.utils.name_list_security import NameListSecurity
from src.utils.emmit_log import log_execution_time, log_execution_time_with_message

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
        log_execution_time(self.management_logs, "IPManager initialized", LogType.START_SESSION, ComponentType.IP_MANAGER, success=True, uuid_agent=0)

    def refresh_lists(self):
        start_time = time.perf_counter()
        self.data_to_save = self.access_list_keeper.load()
        end_time = time.perf_counter()
        log_execution_time_with_message(self.management_logs, "Refreshed lists", LogType.MODIFICATION, ComponentType.IP_MANAGER, start_time, end_time)


    def __move_ip_between_lists(self, ip, from_list: NameListSecurity, to_list: NameListSecurity):
        start_time = time.perf_counter()
        self.management_logs.log_message(ComponentType.IP_MANAGER, f"Moving IP {ip} from {from_list.value} to {to_list.value}", LogType.MODIFICATION)
        from_list_name = from_list.value
        to_list_name = to_list.value
        if ip in self.data_to_save[to_list_name]:
            log_execution_time(self.management_logs, f"Failed to move IP {ip} - Already in {to_list_name}", LogType.ERROR, ComponentType.IP_MANAGER, time=time.perf_counter() - start_time, success=False, uuid_agent=0)
            return ResponseType(
                success=False,
                message=f"The IP {ip} is already in the {to_list_name}.",
                data=None,
                status_ip=None
            )
        if ip in self.data_to_save[from_list_name]:
            self.data_to_save[from_list_name].remove(ip)
            self.management_logs.log_message(ComponentType.IP_MANAGER, f"The IP {ip} removed from {from_list_name}", LogType.MODIFICATION)
        self.data_to_save[to_list_name].add(ip)
        self.management_logs.log_message(ComponentType.IP_MANAGER, "Saving the data.", LogType.SERIALIZATION)
        self.access_list_keeper.save(self.data_to_save)
        end_time = time.perf_counter()
        log_execution_time_with_message(self.management_logs, f"IP {ip} moved from {from_list_name} to {to_list_name}", LogType.END_MODIFICATION, ComponentType.IP_MANAGER, start_time, end_time)
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been moved from the {from_list_name} to the {to_list_name}.",
            data=self.data_to_save[to_list_name],
            status_ip=to_list
        )

    def add_ip_to_list(self, ip, list_type: NameListSecurity):
        start_time = time.perf_counter()
        self.management_logs.log_message(ComponentType.IP_MANAGER, f"Adding IP {ip} to the {list_type.value}", LogType.MODIFICATION)
        list_name = list_type.value
        if list_type in [NameListSecurity.blacklist, NameListSecurity.whitelist]:
            opposite_list = NameListSecurity.blacklist
            if list_type == NameListSecurity.blacklist:
                opposite_list = NameListSecurity.whitelist
            opposite_list = opposite_list.value
            if ip in self.data_to_save[list_name]:
                log_execution_time(self.management_logs, f"Failed to add IP {ip} - Already in {list_name}", LogType.ERROR, ComponentType.IP_MANAGER, time=time.perf_counter() - start_time, success=False, uuid_agent=0)
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} is already in the {list_name}.",
                    data=None,
                    status_ip=list_type
                )
            if ip in self.data_to_save[opposite_list]:
                log_execution_time(self.management_logs, f"Failed to add IP {ip} - Exists in {opposite_list}", LogType.ERROR, ComponentType.IP_MANAGER, time=time.perf_counter() - start_time, success=False, uuid_agent=0)
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} cannot be added to the {list_name} because it is in the {opposite_list}.",
                    data=None,
                    status_ip=opposite_list
                )
        else:
            if ip in self.data_to_save[list_name]:
                log_execution_time(self.management_logs, f"Failed to add IP {ip} - Already in {list_name}", LogType.ERROR, ComponentType.IP_MANAGER, time=time.perf_counter() - start_time, success=False, uuid_agent=0)
                return ResponseType(
                    success=False,
                    message=f"The IP {ip} is already in the {list_name}.",
                    data=None,
                    status_ip=list_type
                )
        self.data_to_save[list_name].add(ip)
        self.management_logs.log_message(ComponentType.IP_MANAGER, f"The IP {ip} has been added to the {list_name}.", LogType.MODIFICATION)
        self.management_logs.log_message(ComponentType.IP_MANAGER, "Saving the data.", LogType.SERIALIZATION)
        self.access_list_keeper.save(self.data_to_save)
        end_time = time.perf_counter()
        log_execution_time_with_message(self.management_logs, f"IP {ip} added to {list_name}", LogType.END_MODIFICATION, ComponentType.IP_MANAGER, start_time, end_time)
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been added to the {list_name}.",
            data=self.data_to_save[list_name],
            status_ip=list_type
        )

    def remove_ip_from_list(self, ip, list_type: NameListSecurity, move_to_list: NameListSecurity = None):
        self.management_logs.log_message(ComponentType.IP_MANAGER, f"Removing IP {ip} from the {list_type.value}", LogType.MODIFICATION)
        if move_to_list:
            return self.__move_ip_between_lists(ip, list_type, move_to_list)
        list_name = list_type.value

        if ip not in self.data_to_save[list_name]:
            return ResponseType(False, f"The IP {ip} is not in the {list_name}.", None, list_type)

        self.management_logs.log_message(ComponentType.IP_MANAGER, f"The IP {ip} has been removed from the {list_name}.", LogType.MODIFICATION)
        self.data_to_save[list_name].remove(ip)
        self.management_logs.log_message(ComponentType.IP_MANAGER, "Saving the data.", LogType.SERIALIZATION)
        self.access_list_keeper.save(self.data_to_save)
        self.management_logs.log_message(ComponentType.IP_MANAGER, "Data saved successfully.", LogType.SERIALIZATION)
        return ResponseType(
            success=True,
            message=f"The IP {ip} has been removed from the {list_name}.",
            data=self.data_to_save[list_name],
            status_ip=list_type
        )

    def check_ip_status(self, ip, id_entity: str):
        start_time = time.perf_counter()
        self.management_logs.log_message(component=ComponentType.IP_MANAGER,message=f"Checking the status of the IP {ip}", uuid_agent=f"{id_entity}", log_type = LogType.VALIDATION, success=True, time_str="0")
        is_blacklisted = ip in self.data_to_save['blacklist']
        is_whitelisted = ip in self.data_to_save['whitelist']
        if is_blacklisted:
            status_messages = f"The IP {ip} is blacklisted."
            log_execution_time_with_message(self.management_logs, f"IP {ip} is blacklisted", LogType.END_VALIDATION, ComponentType.IP_MANAGER, start_time, time.perf_counter(), uuid_agent=id_entity)
            return ResponseType(True, status_messages, NameListSecurity.blacklist, None)
        if is_whitelisted:
            status_messages = f"The IP {ip} is whitelisted."
            log_execution_time_with_message(self.management_logs, f"IP {ip} is whitelisted", LogType.END_VALIDATION, ComponentType.IP_MANAGER, start_time, time.perf_counter(), uuid_agent=id_entity)
            return ResponseType(True, status_messages, NameListSecurity.whitelist, None)
        status_messages = f"The IP {ip} has no specific access status."
        log_execution_time_with_message(self.management_logs, f"IP {ip} has no specific access status", LogType.END_VALIDATION, ComponentType.IP_MANAGER, start_time, time.perf_counter(), uuid_agent=id_entity)
        return ResponseType(False, status_messages, None, None)

    def delete_all_lists(self):
        start_time = time.perf_counter()
        self.management_logs.log_message(ComponentType.IP_MANAGER, "Deleting all lists.", LogType.MODIFICATION)
        self.data_to_save = {
            'blacklist': set(),
            'whitelist': set(),
            'yellow_page_list': set(),
            'logs': '',
            'ultimate_shared_key': '',
            'ultimate_shared_key_agent': ''
        }
        self.management_logs.log_message(ComponentType.IP_MANAGER, "Saving the data.", LogType.SERIALIZATION)
        self.access_list_keeper.save(self.data_to_save)
        end_time = time.perf_counter()
        log_execution_time_with_message(self.management_logs, "All lists deleted and data saved", LogType.END_MODIFICATION, ComponentType.IP_MANAGER, start_time, end_time)
        return ResponseType(
            success=True,
            message="All lists have been cleared.",
            data=None,
            status_ip=None
        )

    def get_ips_in_list(self, list_type: NameListSecurity):
        start_time = time.perf_counter()
        self.management_logs.log_message(ComponentType.IP_MANAGER, f"Getting IPs in the {list_type.value}", LogType.QUERY)
        list_name = list_type.value
        end_time = time.perf_counter()
        log_execution_time_with_message(self.management_logs, f"Retrieved IPs in {list_name}", LogType.END_QUERY, ComponentType.IP_MANAGER, start_time, end_time)
        return ResponseType(
            success=True,
            message=f"IPs in the {list_name}.",
            data=self.data_to_save[list_name],
            status_ip=list_type
        )