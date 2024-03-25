import os
from security.manage_file_security import encrypt_file, decrypt_file
from utils.pyro_config import configure_pyro
from utils.types.save_data_type import SaveDataType

configure_pyro()


class AccessRegister:
    def __init__(self, password: bytes):
        self.name_file = "data/data.enc"
        self.password = password
        if not os.path.exists(self.name_file):
            self.save({
                'whitelist': set(),
                'blacklist': set(),
                'yellow_page_list': set()
            })

    def save(self, data: SaveDataType):
        encrypt_file(self.name_file, self.password, data)

    def load(self) -> SaveDataType:
        data = decrypt_file(self.name_file, self.password)
        return data

    def delete(self):
        os.remove(self.name_file)





