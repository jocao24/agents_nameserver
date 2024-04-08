from src.manage_logs.manage_logs import get_end_session_log, log_message
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

    def _view_logs(self):
        logs = get_end_session_log()
        print(logs)

    def _add_whitelist(self):
        ip = input("Enter the IP you want to add to the whitelist: ")
        is_valid_ip = validate_ip(ip)
        if is_valid_ip:
            data = self.access_coordinator.add_ip_to_list(ip, NameListSecurity.whitelist)
            log_message(data.message)

        else:
            print("The IP entered is not valid. Please enter a valid IP.")

    def _add_blacklist(self):
        ip = input("Enter the IP you want to add to the blacklist: ")
        is_valid_ip = validate_ip(ip)
        if is_valid_ip:
            data = self.access_coordinator.add_ip_to_list(ip, NameListSecurity.blacklist)
            log_message(data.message)
        else:
            print("The IP entered is not valid. Please enter a valid IP.")

    def _view_whitelist(self):
        whitelist = self.access_coordinator.get_ips_in_list(NameListSecurity.whitelist)
        i = 1
        if len(whitelist):
            for ip in whitelist:
                print(f"{i}. {ip}")
                i += 1
        else:
            print("The whitelist is empty.")

    def _view_blacklist(self):
        blacklist = self.access_coordinator.get_ips_in_list(NameListSecurity.blacklist)
        i = 1
        if len(blacklist):
            for ip in blacklist:
                print(f"{i}. {ip}")
            i += 1
        else:
            print("The blacklist is empty.")

    def _remove_ip(self, type_list: NameListSecurity, ip: str):
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
            log_message(response.message)
            print(response.message)

    def _remove_whitelist(self):
        whitelist = self.access_coordinator.get_ips_in_list(NameListSecurity.whitelist)
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
        blacklist = list(self.access_coordinator.get_ips_in_list(NameListSecurity.blacklist))
        self._view_blacklist()
        if len(blacklist):
            is_valid_input = False
            ip = input("Enter the number of the IP you want to remove from the blacklist: ")
            if ip.isdigit():
                ip = int(ip)
                if 0 < ip <= len(blacklist):
                    ip = list(blacklist)[ip - 1]
                    self._remove_ip(NameListSecurity.blacklist, ip)
            if not is_valid_input:
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
        shared_key = self.access_coordinator.generate_shared_key()
        # ANSI escape secuences for bold and underline
        bold = '\033[1m'
        underline = '\033[4m'
        reset = '\033[0m'  # Reset formatting
        # Combinar las secuencias con el texto deseado
        formatted_key = f"{bold}{underline}{shared_key}{reset}"
        print(f"The shared key for registering agents is: {formatted_key}. Please do not share it with anyone.")
        print("Note: This key will be valid for 10 minutes.")

    def get_options(self):
        options = {
            1: "View Shared Key For Registering Agents",
            2: "Add whitelist",
            3: "Add blacklist",
            4: "View whitelist",
            5: "View blacklist",
            6: "Remove whitelist",
            7: "Remove blacklist",
            8: "View logs",
            9: "Exit"
        }

        options_execute = {
            1: self._view_shared_key,
            2: self._add_whitelist,
            3: self._add_blacklist,
            4: self._view_whitelist,
            5: self._view_blacklist,
            6: self._remove_whitelist,
            7: self._remove_blacklist,
            8: self._view_logs,
            9: self._exit
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
