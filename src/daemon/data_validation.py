from src.types.request_data_type import RequestDataType


def is_valid_request_data(request: RequestDataType) -> bool:
    return all(k in request for k in ["iv", "data", "id"])
