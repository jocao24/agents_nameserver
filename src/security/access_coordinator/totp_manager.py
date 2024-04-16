import pyotp
import qrcode
from src.manage_logs.manage_logs import ManagementLogs


class TOTPManager:
    def __init__(self, management_logs):
        self.management_logs = management_logs
        self.secret = pyotp.random_base32()
        self.__generate_secret_token()
        self.management_logs.log_message('TOTPManager -> TOTPManager initialized')

    def __generate_secret_token(self):
        self.management_logs.log_message('TOTPManager -> Generating secret token...')
        token = pyotp.totp.TOTP(self.secret).provisioning_uri(name="CodeSecret", issuer_name="AccesAgent")
        img = qrcode.make(token)
        img.save("data2/qrcode_access.png")
        self.management_logs.log_message('TOTPManager -> Secret token generated')

    def verify_totp(self, otp_received):
        self.management_logs.log_message('TOTPManager -> Verifying TOTP...')
        totp = pyotp.TOTP(self.secret)
        result = totp.verify(otp_received)
        self.management_logs.log_message(f'TOTPManager -> TOTP verified: {result}')
        return result
