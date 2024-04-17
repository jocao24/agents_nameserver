import Pyro5.api
from src.utils.custom_exception import CustomException


def configure_pyro():
    Pyro5.api.SerializerBase.register_class_to_dict(CustomException, CustomException.to_dict)
    Pyro5.api.SerializerBase.register_dict_to_class(CustomException.__name__, CustomException.from_dict)
