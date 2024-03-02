from .errors import ErrorTypes


class CustomException(Exception):
    def __init__(self, error_type: ErrorTypes):
        self.error_type = error_type
        super().__init__(f"{error_type.code}: {error_type.message}")

    def to_dict(self):
        return {"code": self.error_type.code, "message": self.error_type.message}

    @classmethod
    def from_dict(cls, data):
        error_type = ErrorTypes(data["code"])
        return cls(error_type)
