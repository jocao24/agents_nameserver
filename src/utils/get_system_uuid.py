import subprocess
import platform


def get_system_uuid():
    operating_system = platform.system()

    if operating_system == "Windows":
        try:
            output = subprocess.check_output('wmic csproduct get UUID', shell=True).decode()
            uuid = output.split('\n')[1].strip()
            return uuid
        except subprocess.CalledProcessError as e:
            return None
    else:
        try:
            result = subprocess.run(['blkid'], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return None
        uuids = {}
        lines = result.stdout.splitlines()
        for line in lines:
            device_match = re.search(r'^([^:]+):', line)
            uuid_match = re.search(r'UUID="([^"]+)"', line)
            if device_match and uuid_match:
                uuids[device_match.group(1)] = uuid_match.group(1)
        if uuids:
            first_device = next(iter(uuids))
            return uuids[first_device]

        else:
            return None
