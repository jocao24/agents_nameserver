import Pyro5.nameserver


def locate_gateway(nameserver:Pyro5.nameserver.NameServer):
    list_nameserver = nameserver.list()
    for name, uri in list_nameserver.items():
        if "gateway_manager" in name:
            return uri
    return None


def locate_yellow_page(nameserver: Pyro5.nameserver.NameServer, ip_yp: str):
    list_nameserver = nameserver.list()
    name_yp = "yellow_page@" + ip_yp
    for name, uri in list_nameserver.items():
        if name_yp in name:
            return uri
