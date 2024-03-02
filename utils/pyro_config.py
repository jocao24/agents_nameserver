import Pyro4
from utils.custom_exception import CustomException


def configure_pyro():
    Pyro4.util.SerializerBase.register_class_to_dict(CustomException, CustomException.to_dict)
    Pyro4.util.SerializerBase.register_dict_to_class(CustomException.__name__, CustomException.from_dict)
