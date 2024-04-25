import json
import socket

from server.wifi.wifi import get_connection_configs, is_connected, get_ip_address

from ..handler import GetHandler
from ..requestData import RequestData


class NetworkHandler(GetHandler):
    def schema(self):
        return self.create_schema(
            "Returns the list of networks",
            returns={"connections": "list of dicts, containing the configured networks."}
        )

    def do_get(self, data: RequestData):
        return 200, json.dumps({"connections": get_connection_configs()})


class AddressHandler(GetHandler):
    def schema(self):
        return self.create_schema(
            "Returns the IP address of the device",
            returns={"ip": "string, containing the IP local network address of the device. 127.0.0.1 is returned if no network is available.",
                     "port": "int, containing the port of the REST server."}
        )



    def do_get(self, data: RequestData):
        if is_connected():
            return 200, json.dumps({"ip": get_ip_address(), "port": data.bb.rest_server_port})
        else:
            return 200, json.dumps({"ip": "no network", "port": 0})
