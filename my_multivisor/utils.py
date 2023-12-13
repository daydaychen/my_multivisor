import socket


def get_available_port(start=10000, end=11000):
    for port in range(start, end):
        s = socket.socket()
        s.bind(('', 0))
        _, port = s.getsockname()
        s.close()
        return port
