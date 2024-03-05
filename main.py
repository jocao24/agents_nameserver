import signal
import subprocess
import sys
import threading
import time
import Pyro4
from gateway.gateway_manager import GatewayManager
from controller.nameserver_controller import NameServerController
from manage_logs.manage_logs import start_new_session_log, log_message
from utils.custom_exception import CustomException
from utils.pyro_config import configure_pyro
from utils.get_ip import get_ip
import datetime

configure_pyro()
ip_local = get_ip()
port_nameserver = 9090
global_logs = []


def signal_handler(signum, frame):
    log_message("Cierre intencional por el usuario")
    sys.exit(0)


def setup_signal_handlers():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def create_nameserver_space():
    cmd = f"pyro4-ns --host {ip_local} -p 9090"
    subprocess.Popen(cmd, shell=True)
    # print(f"Name Server started in: {ip_local}:9090")
    start_new_session_log()
    global_logs.append(log_message(f"Name Server started in: {ip_local}:9090"))


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
    log_message("Finally. Shutting down...")
    daemon.shutdown()
    sys.exit(0)


def daemon_loop():
    daemon.requestLoop()


if __name__ == '__main__':
    try:
        yp_located_event = threading.Event()
        finally_name_server = threading.Event()
        Pyro4.util.SerializerBase.register_class_to_dict(CustomException, CustomException.__dict__)
        create_nameserver_space()

        if not wait_for_nameserver():
            # print("Error: NameServer did not start correctly.")
            global_logs.append(log_message("Error: NameServer did not start correctly."))
            exit(1)

        daemon = Pyro4.Daemon(host=ip_local, port=9091)
        nameserver = Pyro4.locateNS(host=ip_local, port=port_nameserver)
        # print(f"NameServer located: {nameserver}")
        global_logs.append(log_message(f"NameServer located: {nameserver}"))

        gateway_manager = GatewayManager(yp_located_event, finally_name_server)
        uri_gateway = daemon.register(gateway_manager)
        # print(f"GatewayManager registered with URI: {uri_gateway}")
        global_logs.append(log_message(f"GatewayManager registered with URI: {uri_gateway}"))
        nameserver.register("gateway_manager", uri_gateway)
        yp_located_event.wait()
        ns_controller = NameServerController(nameserver, gateway_manager, gateway_uri=uri_gateway)
        uri_ns_controller = daemon.register(ns_controller)
        nameserver.register("ns_controller", uri_ns_controller)
        # print(f"NameServerController registered with URI: {uri_ns_controller}")
        global_logs.append(log_message(f"NameServerController registered with URI: {uri_ns_controller}"))

        print("NameServer running...")
        log_message("NameServer running...")

        daemon_thread = threading.Thread(target=daemon_loop)
        daemon_thread.start()

        check_finally_thread = threading.Thread(target=check_finally_event)
        check_finally_thread.start()
    except Exception as e:
        print(e)
        log_message(f"Error: {e}")
