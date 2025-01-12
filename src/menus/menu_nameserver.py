from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils.errors import ErrorTypes
from src.utils.separators import show_separators, show_center_text_with_separators
from src.utils.name_list_security import NameListSecurity
from src.utils.validate_ip import validate_ip
from src.manage_logs.manage_logs_v_2 import LogType, ComponentType

class MenuNameServer:
    def __init__(self, access_coordinator: AccessCoordinator, finally_name_server):
        self.access_coordinator = access_coordinator
        self.finally_name_server = finally_name_server
        self.running = True

    def _view_logs_session_active(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Uploading the logs for the current session...", LogType.UPLOAD, True)
        all_logs = self.access_coordinator.management_logs.get_current_session_logs()
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "The logs for the current session have been uploaded successfully.", LogType.END_UPLOAD, True)
        show_center_text_with_separators("Logs Session Active")
        print(all_logs)

    def _view_logs(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Uploading the logs...", LogType.UPLOAD, True)
        all_logs = self.access_coordinator.management_logs.get_all_logs()
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "The logs have been uploaded successfully.", LogType.END_UPLOAD, True)
        print(all_logs)

    def _export_logs_to_csv(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Exporting logs to CSV...", LogType.END_UPLOAD, True)
        try:
            self.access_coordinator.management_logs.export_logs_to_csv()
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Logs have been exported.", LogType.END_UPLOAD, True)
            print("Logs have been exported to data/logs_ns.csv")
        except Exception as e:
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, f"Error exporting logs: {e}", LogType.ERROR, False)
            print(f"Error exporting logs: {e}")

    def _add_whitelist(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Adding an IP to the whitelist...", LogType.ADD_ACL_WHITELIST, True)
        ip = input("Enter the IP you want to add to the whitelist: ")
        is_valid_ip = validate_ip(ip)
        if is_valid_ip:
            data = self.access_coordinator.add_ip_to_list(ip, NameListSecurity.whitelist)
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, data.message, LogType.END_ADD_ACL_WHITELIST, True)
        else:
            print("The IP entered is not valid. Please enter a valid IP.")
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Invalid IP entered for whitelist.", LogType.END_ADD_ACL_WHITELIST, False)

    def _add_blacklist(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Adding an IP to the blacklist...", LogType.ADD_ACL_BLACKLIST, True)
        ip = input("Enter the IP you want to add to the blacklist: ")
        is_valid_ip = validate_ip(ip)
        if is_valid_ip:
            data = self.access_coordinator.add_ip_to_list(ip, NameListSecurity.blacklist)
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, data.message, LogType.END_ADD_ACL_BLACKLIST, True)
        else:
            print("The IP entered is not valid. Please enter a valid IP.")
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Invalid IP entered for blacklist.", LogType.ERROR, False)

    def _view_whitelist(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Uploading the whitelist...", LogType.UPLOAD, True)
        whitelist = self.access_coordinator.get_ips_in_list(NameListSecurity.whitelist).data
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "The whitelist has been uploaded successfully.", LogType.END_UPLOAD, True)

        print(show_separators())
        print(show_center_text_with_separators("Whitelist"))
        print(show_separators())
        whitelist = list(whitelist)[3]

        if whitelist:
            for i, ip in enumerate(whitelist, start=1):
                print(f"{i}. {ip}")
        else:
            print("The whitelist is empty.")
        print(show_separators())

    def _view_blacklist(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Uploading the blacklist...", LogType.UPLOAD, True)
        blacklist = self.access_coordinator.get_ips_in_list(NameListSecurity.blacklist).data
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "The blacklist has been uploaded successfully.", LogType.END_UPLOAD, True)

        print(show_separators())
        print(show_center_text_with_separators("Blacklist"))
        print(show_separators())
        blacklist = list(blacklist)[3]

        if blacklist:
            print(f"Total IPs in the blacklist: {blacklist}")
            for i, ip in enumerate(blacklist, start=1):
                print(f"{i}. {ip}")
        else:
            print("The blacklist is empty.")
        print(show_separators())

    def _remove_ip(self, type_list: NameListSecurity, ip: str):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, f"Removing the IP {ip} from the {type_list.value}...", LogType.DELETE_ACL_WHITELIST if type_list == NameListSecurity.whitelist else LogType.DELETE_ACL_BLACKLIST, True)
        opt_select = input(f"Do you want to add it to the {NameListSecurity.whitelist.value if type_list == NameListSecurity.blacklist else NameListSecurity.blacklist.value}? (y/n): -> default n ")
        if opt_select.lower() != 'n' and opt_select.lower() != 'y' and opt_select != '':
            print(ErrorTypes.invalid_option.message)
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, ErrorTypes.invalid_option.message, LogType.END_DELETE_ACL_WHITELIST if type_list == NameListSecurity.whitelist else LogType.END_DELETE_ACL_BLACKLIST, False)
        else:
            response = None
            if opt_select == '' or opt_select.lower() == 'n':
                if type_list == NameListSecurity.blacklist:
                    response = self.access_coordinator.remove_ip_from_list(ip, NameListSecurity.blacklist)
                else:
                    response = self.access_coordinator.remove_ip_from_list(ip, NameListSecurity.whitelist)

            if opt_select.lower() == 'y':
                if type_list == NameListSecurity.blacklist:
                    response = self.access_coordinator.remove_ip_from_list(ip, NameListSecurity.blacklist, NameListSecurity.whitelist)
                else:
                    response = self.access_coordinator.remove_ip_from_list(ip, NameListSecurity.whitelist, NameListSecurity.blacklist)
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, response.message, LogType.END_DELETE_ACL_WHITELIST if type_list == NameListSecurity.whitelist else LogType.END_DELETE_ACL_BLACKLIST, response.success)
            print(response.message)

    def _remove_whitelist(self):
        whitelist = self.access_coordinator.get_ips_in_list(NameListSecurity.whitelist).data
        self._view_whitelist()
        if len(whitelist):
            ip = input("Enter the number of the IP you want to remove from the whitelist: ")
            if ip.isdigit():
                ip = int(ip)
                if 0 < ip <= len(whitelist):
                    ip = list(whitelist)[ip - 1]
                    self._remove_ip(NameListSecurity.whitelist, ip)
                else:
                    print(ErrorTypes.invalid_option.message)
                    self.access_coordinator.management_logs.log_message(ComponentType.MENU, ErrorTypes.invalid_option.message, LogType.ERROR, False)
            else:
                print(ErrorTypes.invalid_option.message)
                self.access_coordinator.management_logs.log_message(ComponentType.MENU, ErrorTypes.invalid_option.message, LogType.ERROR, False)
        else:
            print("The whitelist is empty.")
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, "The whitelist is empty.", LogType.QUERY, True)

    def _remove_blacklist(self):
        blacklist = self.access_coordinator.get_ips_in_list(NameListSecurity.blacklist).data
        self._view_blacklist()
        if len(blacklist):
            ip = input("Enter the number of the IP you want to remove from the blacklist: ")
            if ip.isdigit():
                ip = int(ip)
                if 0 < ip <= len(blacklist):
                    ip = list(blacklist)[ip - 1]
                    self._remove_ip(NameListSecurity.blacklist, ip)
                else:
                    print(ErrorTypes.invalid_option.message)
                    self.access_coordinator.management_logs.log_message(ComponentType.MENU, ErrorTypes.invalid_option.message, LogType.ERROR, False)
            else:
                print(ErrorTypes.invalid_option.message)
                self.access_coordinator.management_logs.log_message(ComponentType.MENU, ErrorTypes.invalid_option.message, LogType.ERROR, False)
        else:
            print("The blacklist is empty.")
            self.access_coordinator.management_logs.log_message(ComponentType.MENU, "The blacklist is empty.", LogType.QUERY, True)

    def _exit(self):
        self.finally_name_server.set()
        print(show_center_text_with_separators("Exiting..."))
        print(show_separators())
        print("\n")
        self.running = False
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Exiting menu.", LogType.EXIT, True)

    def _view_shared_key(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Generating a shared key...", LogType.KEY_GENERATION, True)
        shared_key = self.access_coordinator.get_shared_key_agent()
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "The shared key has been generated successfully.", LogType.END_KEY_GENERATION, True)
        bold = '\033[1m'
        underline = '\033[4m'
        reset = '\033[0m'
        formatted_key = f"{bold}{underline}{shared_key}{reset}"
        print(f"The shared key for registering agents_remote_objects is: {formatted_key}. Please do not share it with anyone.")

    def register_or_update_shared_key_by_yp(self):
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Registering or updating the shared key provided by the yellow_page...", LogType.KEY_GENERATION, True)
        self.access_coordinator.validate_shared_key()
        self.access_coordinator.management_logs.log_message(ComponentType.MENU, "The shared key has been registered or updated successfully.", LogType.END_KEY_GENERATION, True)

    def get_options(self):
        options = {
            1: "View Shared Key For Registering Agents",
            2: "Register or Update Shared Key Provided by Yellow Page",
            3: "Add IP to Whitelist",
            4: "Add IP to Blacklist",
            5: "View Whitelist",
            6: "View Blacklist",
            7: "Remove IP from Whitelist",
            8: "Remove IP from Blacklist",
            9: "View Logs for Current Session",
            10: "Show All Logs",
            11: "Export Logs to CSV",
            12: "Exit"
        }

        options_execute = {
            1: self._view_shared_key,
            2: self.register_or_update_shared_key_by_yp,
            3: self._add_whitelist,
            4: self._add_blacklist,
            5: self._view_whitelist,
            6: self._view_blacklist,
            7: self._remove_whitelist,
            8: self._remove_blacklist,
            9: self._view_logs_session_active,
            10: self._view_logs,
            11: self._export_logs_to_csv,
            12: self._exit
        }

        return options, options_execute

    def show_menu(self):
        menu, menu_execute = self.get_options()
        while self.running:
            print(show_separators())
            print(show_center_text_with_separators("Menu Options"))
            print(show_separators())
            for key, value in menu.items():
                print(f"{key}. {value}")
            print(show_separators())
            option = input("Enter the number of the option you want to execute: -> ")
            if option.isdigit():
                option = int(option)
                if option in menu_execute:
                    menu_execute[option]()
                else:
                    print(ErrorTypes.invalid_option.message)
                    self.access_coordinator.management_logs.log_message(ComponentType.MENU, ErrorTypes.invalid_option.message, LogType.ERROR, False)
            else:
                print("Invalid option. Please enter a valid option.")
                self.access_coordinator.management_logs.log_message(ComponentType.MENU, "Invalid option entered.", LogType.ERROR, False)
            print(show_separators())

