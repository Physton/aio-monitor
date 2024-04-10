from utils.get_value import get_value
from utils.format import Format
from rich.panel import Panel
import rich.box as Box


def cli_richs(_configs, _data):
    richs = {}

    for sensor in get_value(_configs, 'homeassistant.sensors', []):
        richs[f"ha.{sensor['id']}"] = Panel("", title=Format.bold(sensor['title']), box=Box.SIMPLE)

    richs['pve_power'] = Panel("", title=Format.bold('整机功耗'), box=Box.SIMPLE)
    richs['pve_cpu_count'] = Panel("", title=Format.bold('CPU核心'), box=Box.SIMPLE)
    richs['pve_cpu_freq'] = Panel("", title=Format.bold('CPU频率'), box=Box.SIMPLE)
    richs['pve_cpu_usage'] = Panel("", title=Format.bold('CPU占用'), box=Box.SIMPLE)
    richs['pve_mem_total'] = Panel("", title=Format.bold('内存总量'), box=Box.SIMPLE)
    richs['pve_mem_usage'] = Panel("", title=Format.bold('内存占用'), box=Box.SIMPLE)
    richs['pve_cpu_fan_value'] = Panel("", title=Format.bold('CPU风扇'), box=Box.SIMPLE)
    richs['pve_disk_fan_value'] = Panel("", title=Format.bold('硬盘风扇'), box=Box.SIMPLE)
    richs['pve_cpu_temp_value'] = Panel("", title=Format.bold('CPU温度'), box=Box.SIMPLE)
    richs['pve_nvme_temp_value'] = Panel("", title=Format.bold('M2温度'), box=Box.SIMPLE)

    richs['op_cpu_temp_value'] = Panel("", title=Format.bold('CPU温度'), box=Box.SIMPLE)
    richs['op_cpu_count'] = Panel("", title=Format.bold('CPU核心'), box=Box.SIMPLE)
    richs['op_cpu_freq'] = Panel("", title=Format.bold('CPU频率'), box=Box.SIMPLE)
    richs['op_cpu_usage'] = Panel("", title=Format.bold('CPU占用'), box=Box.SIMPLE)
    richs['op_uptime'] = Panel("", title=Format.bold('系统运行时间'), box=Box.SIMPLE)
    richs['op_mem_total'] = Panel("", title=Format.bold('内存总量'), box=Box.SIMPLE)
    richs['op_mem_usage'] = Panel("", title=Format.bold('内存占用'), box=Box.SIMPLE)
    richs['op_client_num'] = Panel("", title=Format.bold('客户端数'), box=Box.SIMPLE)
    richs['op_connect_num'] = Panel("", title=Format.bold('连接数'), box=Box.SIMPLE)
    richs['op_totaldown'] = Panel("", title=Format.bold('总下载流量'), box=Box.SIMPLE)
    richs['op_totalup'] = Panel("", title=Format.bold('总上传流量'), box=Box.SIMPLE)
    richs['op_download'] = Panel("", title=Format.bold('下载流量'), box=Box.SIMPLE)
    richs['op_upload'] = Panel("", title=Format.bold('上传流量'), box=Box.SIMPLE)

    return richs
