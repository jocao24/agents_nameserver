import os
import signal
import socket
import subprocess
import sys
import threading
import time
import Pyro4

from gateway.class_for_gateway.menu import Menu
from gateway.gateway_manager import GatewayManager
from controller.nameserver_controller import NameServerController
from manage_logs.manage_logs import start_new_session_log, log_message
from security.authenticate import AuthenticationManager
from security.security_deamon import SecureDaemon
from utils.custom_exception import CustomException
from utils.pyro_config import configure_pyro
from utils.get_ip import get_ip
import datetime
from secrets import compare_digest
import getpass

from utils.separators import show_separators, show_center_text_with_separators

configure_pyro()
ip_local = get_ip()
port_nameserver = 9090
global_logs = []
proxy_port = 9099  # El puerto en el que el servidor proxy escuchará
process = None


def signal_handler(signum, frame):
    log_message("Intentional closure by the user")
    sys.exit(0)


def setup_signal_handlers():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def create_nameserver_space():
    cmd = f"pyro4-ns --host {ip_local} -p {port_nameserver}"
    global process
    process = subprocess.Popen(cmd, shell=True)
    start_new_session_log()
    global_logs.append(log_message(f"Name Server started in: {ip_local}:{port_nameserver}"))


def terminate_nameserver_space():
    if process is not None:
        os.system("taskkill /f /im pyro4-ns.exe")
        print("Cleanup complete. Exiting now.")
        process.terminate()
        process.wait()


def wait_for_nameserver():
    for _ in range(10):
        try:
            Pyro4.locateNS(host=ip_local, port=port_nameserver)
            return True
        except Pyro4.errors.NamingError:
            time.sleep(0.1)
    return False


def check_finally_event():
    finally_name_server.wait()
    daemon.shutdown()
    terminate_nameserver_space()
    sys.exit()


def daemon_loop():
    daemon.requestLoop()


if __name__ == '__main__':
    try:
        # Se verifica si existe un archivo dats.enc, si existe se le pide al usuario que ingrese la contraseña.
        # Si no existe, se le pide al usuario que ingrese una contraseña y que la confirme para crear el archivo.
        auth_manager = None
        action = "decrypted"
        print(show_separators())
        print(show_center_text_with_separators("Loading data..."))
        while True:
            if os.path.exists("data/data.enc"):
                print("We found the configuration file What do you want to do with it?")
                print("1. Decrypt the data.")
                print("2. Delete the data and create a new one.")
                print("3. Exit.")
                opt = input("Enter the number of the option you want to perform: ")
                if opt == '1':
                    password = getpass.getpass(prompt="Enter your password: ")
                    auth_manager = AuthenticationManager(password.encode())
                    break
                elif opt.lower() == '2':
                    # Se le pregunta al usuario si está seguro de eliminar los datos.
                    while True:
                        opt_select = input("Are you sure you want to delete the data and create a new one? (y/n): ")
                        if opt_select.lower() == 'y':
                            print("Please enter a password to encrypt the data.")
                            password = getpass.getpass(prompt="Enter your password: ")
                            password_confirm = getpass.getpass(prompt="Confirm your password: ")
                            os.remove("data/data.enc")
                            if compare_digest(password, password_confirm):
                                print("The data has been deleted and a new password has been set.")
                                auth_manager = AuthenticationManager(password.encode())
                                break
                            else:
                                print("Passwords do not match.")
                        elif opt_select.lower() == 'n':
                            break
                        else:
                            print("Invalid option.")
                    break
                elif opt == '3':
                    print(show_separators())
                    print(show_center_text_with_separators("Exiting..."))
                    print(show_separators())
                    sys.exit(0)
                else:
                    print("Invalid option.")
            else:
                print("No data found.")
                print("Please enter a password to encrypt the data.")
                password = getpass.getpass(prompt="Enter your password: ")
                password_confirm = getpass.getpass(prompt="Confirm your password: ")
                if compare_digest(password, password_confirm):
                    auth_manager = AuthenticationManager(password.encode())
                    break
        print(show_separators())
        print(show_center_text_with_separators(f"The information has been {action} successfully."))
        print("A qr code for authentication has been generated in the path: data/qr_code.png")
        print(show_separators() + "\n")

        yp_located_event = threading.Event()
        finally_name_server = threading.Event()
        create_nameserver_space()

        if not wait_for_nameserver():
            global_logs.append(log_message("Error: NameServer did not start correctly."))
            exit(1)

        nameserver = Pyro4.locateNS(host=ip_local, port=port_nameserver)
        daemon = SecureDaemon(nameserver, auth_manager, host=ip_local, port=9091)
        global_logs.append(log_message(f"NameServer located: {nameserver}"))
        menu = Menu(auth_manager, finally_name_server)

        gateway_manager = GatewayManager({
            "auth_manager": auth_manager,
            "nameserver": nameserver,
            "finally_name_server": finally_name_server,
            "deamon": daemon,
            "yp_event": yp_located_event,
            "menu": menu,
        })
        uri_gateway = daemon.register(gateway_manager)
        nameserver.register("gateway_manager", uri_gateway)
        global_logs.append(log_message(f"GatewayManager registered with URI: {uri_gateway}"))
        daemon_thread = threading.Thread(target=daemon_loop, daemon=True)
        daemon_thread.start()
        while not yp_located_event.is_set():
            if finally_name_server.is_set():
                print("The maximum waiting limit has been reached.")
                print("The yellow_page is not registered or is not active.")
                terminate_nameserver_space()
                sys.exit(1)
            time.sleep(1)
        menu.show_menu()

        check_finally_thread = threading.Thread(target=check_finally_event, daemon=True)
        check_finally_thread.start()

    except Exception as e:
        print(e)
        log_message(f"Error: {e}")
    finally:
        terminate_nameserver_space()
