import threading
import Pyro4
import sys
import time
from src.manage_logs.manage_logs_v_2 import ComponentType, LogType, ManagementLogs
from src.menus.menu_nameserver import MenuNameServer
from src.gateway.gateway_manager import GatewayManager
from src.daemon.deamon import Daemon
from src.config.settings import port_nameserver, ip_local
from src.nameserver.nameserver_control import (create_nameserver_space, wait_for_nameserver, terminate_nameserver_space,
                                               check_finally_event, daemon_loop)
from src.security.access_coordinator.access_coordinator import AccessCoordinator
from src.security.access_coordinator.data_management import DataManagement
from src.utils.pyro_config import configure_pyro

configure_pyro()
global_logs = []

if __name__ == '__main__':
    data_management_instance = DataManagement()
    manage_logs = ManagementLogs(data_management_instance)
    try:
        manage_logs.start_new_session_log()
        access_coordinator = AccessCoordinator(manage_logs)
        yp_located_event = threading.Event()
        finally_name_server = threading.Event()
        create_nameserver_space(manage_logs)

        if not wait_for_nameserver():
            global_logs.append(manage_logs.log_message(ComponentType.NAMESERVER, "Error: NameServer did not start correctly.", LogType.ERROR, False))
            exit(1)

        nameserver = Pyro4.locateNS(host=ip_local, port=port_nameserver)
        daemon = Daemon(nameserver, access_coordinator, host=ip_local, port=9091)
        global_logs.append(manage_logs.log_message(ComponentType.NAMESERVER, f"NameServer located: {nameserver}", LogType.CONNECTION, True))
        menu = MenuNameServer(access_coordinator, finally_name_server)

        gateway_manager = GatewayManager({
            "access_coordinator": access_coordinator,
            "nameserver": nameserver,
            "finally_name_server": finally_name_server,
            "deamon": daemon,
            "yp_event": yp_located_event,
            "menu": menu,
        })
        uri_gateway = daemon.register(gateway_manager)
        nameserver.register("gateway_manager", uri_gateway)
        global_logs.append(manage_logs.log_message(ComponentType.NAMESERVER, f"GatewayManager registered with URI: {uri_gateway}", LogType.REGISTRATION, True))
        daemon_thread = threading.Thread(target=daemon_loop, daemon=True, args=(daemon, manage_logs))
        daemon_thread.start()
        while not yp_located_event.is_set():
            if finally_name_server.is_set():
                print("The maximum waiting limit has been reached.")
                print("The yellow_page is not registered or is not active.")
                terminate_nameserver_space(manage_logs)
                sys.exit(1)
            time.sleep(1)
        menu.show_menu()

        check_finally_thread = threading.Thread(target=check_finally_event, daemon=True, args=(finally_name_server, daemon, manage_logs))
        check_finally_thread.start()

    except Exception as e:
        print(e)
        manage_logs.log_message(ComponentType.NAMESERVER, f"Error: {e}", LogType.ERROR, False)
    finally:
        terminate_nameserver_space(manage_logs)
