import os
import pyotp
import qrcode
from src.manage_logs.manage_logs_v_2 import ManagementLogs
from src.manage_logs.manage_logs_v_2 import LogType, ComponentType

class TOTPManager:
    def __init__(self, management_logs: ManagementLogs):
        self.management_logs = management_logs
        self.secret = pyotp.random_base32()
        self.__generate_secret_token()
        self.management_logs.log_message(ComponentType.TOTP_MANAGER, 'TOTPManager initialized', LogType.START_SESSION)

    def __generate_secret_token(self):
        self.management_logs.log_message(ComponentType.TOTP_MANAGER, 'Generating secret token...', LogType.KEY_GENERATION)
        token = pyotp.totp.TOTP(self.secret).provisioning_uri(name="CodeSecret", issuer_name="AccesAgent")
        img = qrcode.make(token)
        # Obtén la ruta del directorio actual (el que contiene el script que se está ejecutando)
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Navega dos nivel hacia atrás para ubicarte en el directorio que contiene 'src'
        project_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir, os.pardir))
        print(project_root)

        # Concatena la carpeta 'data' a la ruta del proyecto
        data_dir = os.path.join(project_root, 'data') + os.sep
        img.save(f"{data_dir}qrcode_access.png")
        self.management_logs.log_message(ComponentType.TOTP_MANAGER, 'Secret token generated', LogType.END_KEY_GENERATION, True)

    def verify_totp(self, otp_received):
        self.management_logs.log_message(ComponentType.TOTP_MANAGER, 'Verifying TOTP...', LogType.VALIDATION_TOTP)
        totp = pyotp.TOTP(self.secret)
        result = totp.verify(otp_received)
        self.management_logs.log_message(ComponentType.TOTP_MANAGER, f'TOTP verified: {result}', LogType.END_VALIDATION_TOTP, result)
        return result
