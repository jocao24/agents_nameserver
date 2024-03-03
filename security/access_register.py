import json
import os
from utils.pyro_config import configure_pyro

configure_pyro()


class AccessRegister:
    def set_register_access(self, key, data):
        if os.path.exists("access_data.json"):
            with open("access_data.json", "r") as f:
                all_data = json.load(f)
        else:
            all_data = {}
        all_data[key] = list(data)
        with open("access_data.json", "w") as f:
            json.dump(all_data, f)

    def get_register_access(self, key):
        if os.path.exists("access_data.json"):
            with open("access_data.json", "r") as f:
                data = json.load(f)
                return set(data.get(key, []))
        return set()
