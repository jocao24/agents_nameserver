import os
import signal
import subprocess
import time
import Pyro4
import sys
from src.config.settings import ip_local, port_nameserver
from src.manage_logs.manage_logs_v_2 import ComponentType, LogType, ManagementLogs
from src.utils.emmit_log import log_execution_time, log_execution_time_with_message

global process
global_logs = []


def signal_handler(signum, frame):
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sys.exit(0)

def create_nameserver_space(manage_logs: ManagementLogs):
    start_time = time.perf_counter()
    cmd = f"pyro4-ns --host {ip_local} -p {port_nameserver}"
    global process
    process = subprocess.Popen(cmd, shell=True)
    manage_logs.start_new_session_log()
    global_logs.append(manage_logs.log_message(ComponentType.NAMESERVER_CONTROL, f"Name Server started in: {ip_local}:{port_nameserver}", LogType.DAEMON_START, True))
    end_time = time.perf_counter()
    log_execution_time_with_message(manage_logs, "NameServer space creation", LogType.END_DAEMON_START, ComponentType.NAMESERVER_CONTROL, start_time, end_time)

def terminate_nameserver_space(manage_logs: ManagementLogs):
    start_time = time.perf_counter()
    if process is not None:
        os.system("taskkill /f /im pyro4-ns.exe")
        print("Cleanup complete. Exiting now.")
        manage_logs.log_message(ComponentType.NAMESERVER_CONTROL, "Cleanup complete. Exiting now.", LogType.DAEMON_START, True)
        process.terminate()
        process.wait()
    end_time = time.perf_counter()
    log_execution_time(manage_logs, "Terminate NameServer space", LogType.END_DAEMON_START, ComponentType.NAMESERVER_CONTROL, end_time - start_time)
    os._exit(0)

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
    manage_logs.log_message(ComponentType.NAMESERVER_CONTROL, "Daemon loop started", LogType.DAEMON_START, True)
    daemon.requestLoop()
