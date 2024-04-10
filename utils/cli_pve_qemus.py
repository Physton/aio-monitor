from utils.get_value import get_value
from utils.format import Format
from rich.table import Table
import rich.box as Box


def cli_pve_qemus(_configs, _data, _richs, _layout):
    if _data['pve_enabled']:
        pve_qemus_table = Table(show_header=True, header_style="bold", box=Box.SIMPLE, expand=True)
        pve_qemus_table.add_column("PVE虚拟机状态", justify="center", no_wrap=True)
        pve_qemus_table.add_column("ID", justify="center", no_wrap=True)
        pve_qemus_table.add_column("名称", justify="left", no_wrap=True)
        pve_qemus_table.add_column("类型", justify="center", no_wrap=True)
        pve_qemus_table.add_column("CPU核心", justify="center", no_wrap=True)
        pve_qemus_table.add_column("CPU占用", justify="right", no_wrap=True)
        pve_qemus_table.add_column("内存总量", justify="right", no_wrap=True)
        pve_qemus_table.add_column("内存占用", justify="right", no_wrap=True)
        pve_qemus_table.add_column("流入流量", justify="right", no_wrap=True)
        pve_qemus_table.add_column("流出流量", justify="right", no_wrap=True)

        for qemu in get_value(_data, 'pve_qemus', []):
            pve_qemus_table.add_row(
                Format.green('running') if qemu['status'] == 'running' else Format.red(qemu['status']),
                str(qemu['vmid']),
                qemu['name'],
                qemu['type'],
                f"{qemu['maxcpu']} 核",
                Format.usage(qemu['cpu'], True),
                Format.size(qemu['maxmem'], True),
                Format.size(qemu['mem'], True),
                Format.size(qemu['netin'], True),
                Format.size(qemu['netout'], True),
            )
        _layout["QemuList"].update(pve_qemus_table)
