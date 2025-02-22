# encoding: utf-8

import socket


def check_futu_gateway_avalable(host="127.0.0.1", port=11111):
    """测试host:port是否能连通"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        if result == 0:
            return True
        else:
            return False
    except Exception:
        return False
