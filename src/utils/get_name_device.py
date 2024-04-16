import platform
import socket
import subprocess

from src.manage_logs.manage_logs import ManagementLogs


def ping_device(ip: str, management_logs: ManagementLogs) -> bool:
    # Determina el comando de ping basado en el sistema operativo
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', ip]

    try:
        # Ejecuta el comando de ping con un timeout de 1 segundo
        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
        return output.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        management_logs.log_message(f"An error occurred during ping: {e}")
        return False


def get_name_device(ip: str, management_logs: ManagementLogs):
    if ping_device(ip, management_logs):
        try:
            name = socket.gethostbyaddr(ip)
            return name[0]
        except Exception as e:
            management_logs.log_message(f"An error occurred while trying to get the name of the device: {e}")
    else:
        management_logs.log_message("Device is inactive or ping timed out")
    return None
