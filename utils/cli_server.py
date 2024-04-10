from utils.get_value import get_value
from utils.format import Format
from rich.table import Table
import rich.box as Box


def cli_server(_configs, _data, _richs, _layout):
    if _data['server_enabled']:
        server_table = Table(show_header=True, header_style="bold", box=Box.SIMPLE, expand=True)
        server_table.add_column("服务列表", justify="center", no_wrap=True)
        server_table.add_column("本地", justify="left", no_wrap=True)
        server_table.add_column("本地延迟", justify="right", no_wrap=True)
        server_table.add_column("本地端口", justify="right", no_wrap=True)
        server_table.add_column("公网", justify="left", no_wrap=True)
        server_table.add_column("公网延迟", justify="right", no_wrap=True)
        server_table.add_column("公网端口", justify="right", no_wrap=True)
        for address in get_value(_configs, 'addresses', []):
            server_table.add_row(
                address['name'],
                f"{address['local']}:{address['local_port']}",
                Format.timeout(address, 'local_timeout'),
                Format.port(address, 'local_port_status'),
                # f"{address['public']}:{address['public_port']}",
                f"{address['public_port']}",
                Format.timeout(address, 'public_timeout'),
                Format.port(address, 'public_port_status'),
            )
        _layout["ServiceList"].update(server_table)
