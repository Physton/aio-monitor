from utils.get_value import get_value
from utils.format import Format
from rich.table import Table
import rich.box as Box


def cli_dsm_disks(_configs, _data, _richs, _layout):
    if _data['dsm_enabled']:
        disks_table = Table(show_header=True, header_style="bold", box=Box.SIMPLE, expand=True)
        disks_table.add_column("NAS存储", justify="center", no_wrap=True)
        disks_table.add_column("型号", justify="left", no_wrap=True)
        disks_table.add_column("序列号", justify="left", no_wrap=True)
        disks_table.add_column("容量", justify="right", no_wrap=True)
        disks_table.add_column("温度", justify="right", no_wrap=True)
        disks_table.add_column("读取", justify="right", no_wrap=True)
        disks_table.add_column("写入", justify="right", no_wrap=True)
        for disk in get_value(_data, 'dsm_storage.data.disks', []):
            disks_table.add_row(
                disk['id'],
                disk['model'],
                disk['serial'],
                Format.size(disk['size_total'], True),
                Format.hdd_temp(disk['temp'], True) if disk['diskType'] == 'SATA' else Format.temp(disk['temp'], True),
                Format.size(disk['utilization']['read_byte'], True) if disk['utilization'] else Format.yellow(
                    'loading'),
                Format.size(disk['utilization']['write_byte'], True) if disk['utilization'] else Format.yellow(
                    'loading'),
            )
        _layout["DiskList"].update(disks_table)
