import os
from Pyro4.util import json


class ManageDataNameServer:
    def save_config(self, ip_yellow_page: str):
        if not os.path.exists('data'):
            os.makedirs('data')
        with open(f'data/config.json', 'w') as file:
            json.dump({"ip_yellow_page": ip_yellow_page}, file)

    def get_config(self) -> str:
        try:
            with open(f'data/config.json', 'r') as file:
                data = json.load(file)
                return data['ip_yellow_page']
        except FileNotFoundError:
            return None
