from manage_logs.manage_logs import get_end_session_log
from security.authenticate import AuthenticationManager
from utils.errors import ErrorTypes
from utils.separators import show_separators, show_center_text_with_separators
from utils.name_list_security import NameListSecurity
from utils.validate_ip import validate_ip


class Menu:
    def __init__(self, auth_manager: AuthenticationManager, finally_name_server):
        self.auth_manager = auth_manager
        self.finally_name_server = finally_name_server
        self.running = True

    def _view_logs(self):
        logs = get_end_session_log()
        print(logs)

    def _add_whitelist(self):
        ip = input("Enter the IP you want to add to the whitelist: ")
        is_valid_ip = validate_ip(ip)
        if is_valid_ip:
            messages = self.auth_manager.add_whhite_list(ip)
            for message in messages:
                print(message)
        else:
            print("The IP entered is not valid. Please enter a valid IP.")

    def _add_blacklist(self):
        ip = input("Enter the IP you want to add to the blacklist: ")
        is_valid_ip = validate_ip(ip)
        if is_valid_ip:
            messages = self.auth_manager.add_blacklist(ip)
            for message in messages:
                print(message)
        else:
            print("The IP entered is not valid. Please enter a valid IP.")

    def _view_whitelist(self):
        whitelist = self.auth_manager.get_whitelist()
        i = 1
        if len(whitelist):
            for ip in whitelist:
                print(f"{i}. {ip}")
                i += 1
        else:
            print("The whitelist is empty.")

    def _view_blacklist(self):
        blacklist = self.auth_manager.get_blacklist()
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
            if type_list == NameListSecurity.blacklist:
                messages = self.auth_manager.remove_blacklist(ip)
            else:
                messages = self.auth_manager.remove_whitelist(ip)
            if opt_select.lower() == 'y':
                if type_list == NameListSecurity.blacklist:
                    messages = self.auth_manager.add_whhite_list(ip)
                else:
                    messages = self.auth_manager.add_blacklist(ip)
            for message in messages:
                print(message)

    def _remove_whitelist(self):
        whitelist = self.auth_manager.get_whitelist()
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
        blacklist = list(self.auth_manager.get_blacklist())
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
        # Shutdown daemon and join threads
        if hasattr(self, 'daemon'):
            self.daemon.shutdown()  # Properly shutdown the Pyro4 daemon
        if hasattr(self, 'daemon_thread'):
            self.daemon_thread.join()  # Wait for daemon thread to finish
        if hasattr(self, 'check_finally_thread'):
            self.check_finally_thread.join()  # Wait for check_finally thread to finish

    def _view_shared_key(self):
        shared_key = self.auth_manager.generate_new_key()
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
