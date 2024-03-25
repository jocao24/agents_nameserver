from enum import Enum


class ErrorTypes(Enum):
    otp_required = ("otp_required", "An OTP code is required to authenticate to the GatewayManager.")
    otp_incorrect = ("otp_incorrect", "Incorrect OTP code. Please try again.")
    ip_blocked = ("ip_blocked", "Your IP has been blocked for multiple unsuccessful attempts.")
    ip_not_allowed = ("ip_not_allowed", "Your IP is not authorized for operations.")
    parameters_invalid = ("parameters_invalid", "The parameters are not valid.")
    gateway_uri_required = ("gateway_uri_required", "A URI is required to communicate with the GatewayManager.")
    type_entity_required = ("type_entity_required", "An entity type is required to authenticate to the GatewayManager.")
    description_required = ("description_required", "A description is required to authenticate to the GatewayManager.")
    name_entity_required = ("name_entity_required", "A name is required to authenticate to the GatewayManager.")
    gateway_not_found = ("gateway_not_found", "GatewayManager not found.")
    error_unknown = ("error_unknown", "Unknown error.")
    id_entity_required = ("id_entity_required", "An ID is required to authenticate to the GatewayManager.")
    invalid_uuid = ("invalid_uuid", "The entity ID is not valid.")
    invalid_ip = ("invalid_ip", "The IP entered is not valid. Please enter a valid IP.")
    invalid_option = ("invalid_option", "The option entered is not valid. Please enter a valid option.")
    yellow_page_not_found = ("yellow_page_not_found", "The yellow_page is not registered or is not active.")
    yp_not_registered = ("yp_not_registered", "The yellow_page is not registered or is not active.")
    password_incorrect = ("password_incorrect", "The password entered is incorrect.")
    error_encryption = ("error_encryption", "An error occurred while trying to encrypt the data.")
    invalid_request = ("invalid_request", "The request is not valid.")

    def __init__(self, code, message):
        self.code = code
        self.message = message
