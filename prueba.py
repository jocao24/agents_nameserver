from security.authenticate import AuthenticationManager
from utils.types.save_data_type import SaveDataType

password = 'password'.encode()
data = AuthenticationManager(password)
data_ns: SaveDataType = {
    'whitelist': set(),
    'blacklist': set(),
    'yellow_page_list': set()
}
data.access_registers.save(data_ns)

data_ns = data.access_registers.load()

print(data_ns)
