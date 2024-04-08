import os
import signal
import subprocess
import time
import Pyro4
import sys
from src.manage_logs.manage_logs import log_message, start_new_session_log
from src.config.settings import ip_local, port_nameserver

global process
global_logs = []


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


def check_finally_event(finally_name_server, daemon):
    finally_name_server.wait()
    daemon.shutdown()
    terminate_nameserver_space()
    sys.exit()


def daemon_loop(daemon: Pyro4.Daemon):
    daemon.requestLoop()
