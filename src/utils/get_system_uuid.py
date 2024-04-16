import subprocess
import platform


def get_system_uuid():
    operating_system = platform.system()

    if operating_system == "Windows":
        try:
            # Execute command to get the BIOS UUID in Windows
            output = subprocess.check_output('wmic csproduct get UUID', shell=True).decode()
            # Filter output to get only the UUID
            uuid = output.split('\n')[1].strip()
            return uuid
        except subprocess.CalledProcessError as e:
            print(f"Error obtaining UUID on Windows: {e}")
            return None

    elif operating_system == "Linux":
        try:
            # Open and read the file containing the UUID in Linux
            with open('/sys/class/dmi/id/product_uuid', 'r') as file:
                uuid = file.read().strip()
            return uuid
        except FileNotFoundError as e:
            print(f"UUID file not found on Linux: {e}")
            return None

    else:
        print(f"Operating system '{operating_system}' not supported for this operation.")
        return None

