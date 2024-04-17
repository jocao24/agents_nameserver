from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.utils.errors import ErrorTypes
from src.utils.separators import show_separators, show_center_text_with_separators
from src.utils.name_list_security import NameListSecurity
from src.utils.validate_ip import validate_ip


class MenuNameServer:
    def __init__(self, access_coordinator: AccessCoordinator, finally_name_server):
        self.access_coordinator = access_coordinator
        self.finally_name_server = finally_name_server
        self.running = True

    def _view_logs_session_active(self):
        self.access_coordinator.management_logs.self.access_coordinator.management_logs.log_message("Uploading the logs...")
        all_logs = self.access_coordinator.management_logs.get_all_logs()
        self.access_coordinator.management_logs.self.access_coordinator.management_logs.log_message("The logs have been uploaded successfully.")
        last_session_start_index = all_logs.rfind("===== New Session Started =====")
        if last_session_start_index != -1:
            last_session_logs = all_logs[last_session_start_index:]
        else:
            last_session_logs = all_logs
        show_center_text_with_separators("Logs Session Active")
        print(last_session_logs[len("===== New Session Started =====\n"):])

    def _view_logs(self):
        self.access_coordinator.management_logs.log_message("Uploading the logs...")
        all_logs = self.access_coordinator.management_logs.get_all_logs()
        self.access_coordinator.management_logs.log_message("The logs have been uploaded successfully.")
        print(all_logs)

    def _add_whitelist(self):
        self.access_coordinator.management_logs.log_message("Adding an IP to the whitelist...")
        ip = input("Enter the IP you want to add to the whitelist: ")
        is_valid_ip = validate_ip(ip)
        if is_valid_ip:
            data = self.access_coordinator.add_ip_to_list(ip, NameListSecurity.whitelist)
            self.access_coordinator.management_logs.log_message(data.message)
        else:
            print("The IP entered is not valid. Please enter a valid IP.")

    def _add_blacklist(self):
        self.access_coordinator.management_logs.log_message("Adding an IP to the blacklist...")
        ip = input("Enter the IP you want to add to the blacklist: ")
        is_valid_ip = validate_ip(ip)
        if is_valid_ip:
            data = self.access_coordinator.add_ip_to_list(ip, NameListSecurity.blacklist)
            self.access_coordinator.management_logs.log_message(data.message)
        else:
            print("The IP entered is not valid. Please enter a valid IP.")

    def _view_whitelist(self):
        """Displays the whitelist in a structured format."""
        self.access_coordinator.management_logs.log_message("Uploading the whitelist...")
        whitelist = self.access_coordinator.get_ips_in_list(NameListSecurity.whitelist)
        self.access_coordinator.management_logs.log_message("The whitelist has been uploaded successfully.")

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
        """Displays the blacklist in a structured format."""
        self.access_coordinator.management_logs.log_message("Uploading the blacklist...")
        blacklist = self.access_coordinator.get_ips_in_list(NameListSecurity.blacklist)
        self.access_coordinator.management_logs.log_message("The blacklist has been uploaded successfully.")

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

    def _remove_ip(self, type_list: NameListSecurity, ip: str):
        self.access_coordinator.management_logs.log_message(f"Removing the IP {ip} from the {type_list.value}...")
        opt_select = input(f"Do you want to add it to the {type_list.whitelist.value} ? (y/n): -> default n ")
        if opt_select.lower() != 'n' and opt_select.lower() != 'y' and opt_select != '':
            print(ErrorTypes.invalid_option.message)
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
            self.access_coordinator.management_logs.log_message(response.message)
            print(response.message)

    def _remove_whitelist(self):
        whitelist = list(self.access_coordinator.get_ips_in_list(NameListSecurity.whitelist))[3]
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
            else:
                print(ErrorTypes.invalid_option.message)
        else:
            print("The whitelist is empty.")

    def _remove_blacklist(self):
        blacklist = list(self.access_coordinator.get_ips_in_list(NameListSecurity.blacklist))[3]
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
        else:
            print("The blacklist is empty.")

    def _exit(self):
        self.finally_name_server.set()
        print(show_center_text_with_separators("Exiting..."))
        print(show_separators())
        print("\n")
        self.running = False
        if hasattr(self, 'daemon'):
            self.daemon.shutdown()
        if hasattr(self, 'daemon_thread'):
            self.daemon_thread.join()
        if hasattr(self, 'check_finally_thread'):
            self.check_finally_thread.join()

    def _view_shared_key(self):
        self.access_coordinator.management_logs.log_message("Generating a shared key...")
        shared_key = self.access_coordinator.get_shared_key_agent()
        self.access_coordinator.management_logs.log_message("The shared key has been generated successfully.")
        bold = '\033[1m'
        underline = '\033[4m'
        reset = '\033[0m'
        formatted_key = f"{bold}{underline}{shared_key}{reset}"
        print(f"The shared key for registering agents_remote_objects is: {formatted_key}. Please do not share it with anyone.")

    def register_or_update_shared_key_by_yp(self):
        self.access_coordinator.management_logs.log_message("Registering or updating the shared key provided by the yellow_page...")
        self.access_coordinator.validate_shared_key()
        self.access_coordinator.management_logs.log_message("The shared key has been registered or updated successfully.")

    def get_options(self):
        options = {
            1: "View Shared Key For Registering Agents",
            2: "Register or Update Shared Key Proporciated by Yellow Page",
            3: "Add whitelist",
            4: "Add blacklist",
            5: "View whitelist",
            6: "View blacklist",
            7: "Remove whitelist",
            8: "Remove blacklist",
            9: "View logs session active",
            10: 'Show all logs',
            11: "Exit"
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
            11: self._exit
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
            else:
                print("Invalid option. Please enter a valid option.")
            print(show_separators())
