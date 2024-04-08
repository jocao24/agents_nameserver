import pyotp
import qrcode


class TOTPManager:
    def __init__(self):
        self.secret = pyotp.random_base32()
        self.__generate_secret_token()

    def __generate_secret_token(self):
        token = pyotp.totp.TOTP(self.secret).provisioning_uri(name="CodeSecret", issuer_name="AccesAgent")
        img = qrcode.make(token)
        img.save("data/qrcode_access.png")

    def verify_totp(self, otp_received):
        totp = pyotp.TOTP(self.secret)
        return totp.verify(otp_received)
