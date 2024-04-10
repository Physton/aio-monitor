import socket
from utils.get_value import get_value


def check_port(_configs, _data, _log, address, port):
    try:
        # 创建一个socket对象
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 设置超时时间为5秒
        # 尝试连接
        sock.connect((address, port))
        # 关闭连接
        sock.close()
        _set_port_status(_configs, _data, _log, address, port, True)
    except (socket.timeout, ConnectionRefusedError, socket.gaierror) as e:
        _log.write(f'_check_port {address}:{port} {str(e)}')
        _set_port_status(_configs, _data, _log, address, port, False)
    except Exception as e:
        _log.write(f'_check_port {address}:{port} {str(e)}')
        _set_port_status(_configs, _data, _log, address, port, False)


def _set_port_status(_configs, _data, _log, address, port, status):
    for item in get_value(_configs, 'addresses', []):
        if item['local'] == address and item['local_port'] == port:
            item['local_port_status'] = status
        if item['public'] == address and item['public_port'] == port:
            item['public_port_status'] = status
