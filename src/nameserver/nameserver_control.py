import os
import signal
import subprocess
import time
import Pyro4
import sys
from src.config.settings import ip_local, port_nameserver
from src.manage_logs.manage_logs import ManagementLogs

global process
global_logs = []


def signal_handler(signum, frame):
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sys.exit(0)


def create_nameserver_space(manage_logs: ManagementLogs):
    cmd = f"pyro4-ns --host {ip_local} -p {port_nameserver}"
    global process
    process = subprocess.Popen(cmd, shell=True)
    manage_logs.start_new_session_log()
    global_logs.append(manage_logs.log_message(f"Name Server started in: {ip_local}:{port_nameserver}"))


def terminate_nameserver_space(manage_logs: ManagementLogs):
    if process is not None:
        os.system("taskkill /f /im pyro4-ns.exe")
        print("Cleanup complete. Exiting now.")
        manage_logs.log_message("Cleanup complete. Exiting now.")
        os._exit(0)
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


def check_finally_event(finally_name_server, daemon, manage_logs: ManagementLogs):
    finally_name_server.wait()
    daemon.shutdown()
    terminate_nameserver_space(manage_logs)
    sys.exit()


def daemon_loop(daemon: Pyro4.Daemon, manage_logs: ManagementLogs):
    manage_logs.log_message("Daemon loop started")
    daemon.requestLoop()
