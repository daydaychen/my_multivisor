import socket
import threading
import time
from functools import cached_property
from http import HTTPStatus

import requests
from multivisor.rpc import MultivisorNamespaceRPCInterface
from multivisor.util import sanitize_url
from supervisor.events import getEventNameByType
from supervisor.loggers import getLogger, handle_stdout

from .utils import get_available_port


_format = "%(asctime)s %(levelname)s %(message)s\n"
logger = getLogger(None)
handle_stdout(logger, _format)


# 继承MultivisorNamespaceRPCInterface, 启动注册线程
class CustomMultivisor(MultivisorNamespaceRPCInterface):
    def __init__(self, supervisord, bind, server):
        super().__init__(supervisord, bind["url"])
        Register(self, server, bind).start()

    def _process_event(self, event):
        event_name = getEventNameByType(event.__class__)
        if event_name and not event_name.startswith("PROCESS_LOG"):
            super()._process_event(event)


class Register(threading.Thread):
    def __init__(self, multivisor, server, bind):
        super().__init__(daemon=True, name="MultivisorRegister")
        self.multivisor = multivisor
        server = sanitize_url(server, protocol="http")
        self.server_url = server["url"]
        self.bind = bind
        self.register_api = f"{self.server_url}/api/admin/register"
        self.supervisor_info_api = f"{self.server_url}/api/admin/supervisor/info"

    def is_registered(self):
        try:
            res = requests.post(self.supervisor_info_api, data=self.host_info)
            stat = res.status_code == HTTPStatus.CONFLICT
            return stat
        except requests.exceptions.RequestException:
            return False

    def do_register(self):
        try:
            res = requests.post(self.register_api, data=self.host_info, timeout=5)
            if res.status_code == HTTPStatus.OK:
                logger.info("register success")
            elif res.status_code == HTTPStatus.CONFLICT:
                logger.info("node already exists")
            elif res.status_code == HTTPStatus.LOCKED:
                logger.info("resource busy, retry")
            else:
                logger.info(f"unknown status code: {res.status_code}")
        except requests.exceptions.RequestException:
            logger.warn("server not response, register failed, retry")

    def wait_server(self):
        while not self.multivisor._server:  # noqa
            time.sleep(5)

    @cached_property
    def host_info(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        addr = f"{ip}{self.bind['port']}"
        logger.info(f"server: {self.server_url}, client: {addr}")
        return {"hostname": hostname, "addr": addr}

    def run(self):
        self.wait_server()
        while True:
            if not self.is_registered():
                self.do_register()
            time.sleep(10)


def make_rpc_interface(supervisord, bind="", server=None):
    if not server:
        raise ValueError("field 'server' is required!")
    port = get_available_port()
    url = sanitize_url(bind, protocol="tcp", host="*", port=port)
    multivisor = CustomMultivisor(supervisord, url, server)
    multivisor._start()  # noqa
    return multivisor
