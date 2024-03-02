import subprocess
import time
import Pyro4
from gateway.gateway_manager import GatewayManager
from controller.nameserver_controller import NameServerController
from utils.custom_exception import CustomException
from utils.pyro_config import configure_pyro
from utils.get_ip import get_ip

configure_pyro()
ip_local = get_ip()
port_nameserver = 9090


def create_nameserver_space():
    cmd = f"pyro4-ns --host {ip_local} -p 9090"
    subprocess.Popen(cmd, shell=True)
    print(f"Name Server started in: {ip_local}:9090")


def wait_for_nameserver():
    for _ in range(10):
        try:
            Pyro4.locateNS(host=ip_local, port=port_nameserver)
            return True
        except Pyro4.errors.NamingError:
            time.sleep(0.1)
    return False


if __name__ == '__main__':
    Pyro4.util.SerializerBase.register_class_to_dict(CustomException, CustomException.__dict__)
    create_nameserver_space()

    if not wait_for_nameserver():
        print("Error: NameServer did not start correctly.")
        exit(1)

    daemon = Pyro4.Daemon(host=ip_local, port=9091)
    nameserver = Pyro4.locateNS(host=ip_local, port=port_nameserver)
    print(f"NameServer located: {nameserver}")

    gateway = GatewayManager()
    uri_gateway = daemon.register(gateway)
    print(f"GatewayManager registered with URI: {uri_gateway}")
    nameserver.register("gateway_manager", uri_gateway)

    ns_controller = NameServerController(nameserver, gateway, gateway_uri=uri_gateway)
    uri_ns_controller = daemon.register(ns_controller)
    nameserver.register("ns_controller", uri_ns_controller)

    daemon.requestLoop()
