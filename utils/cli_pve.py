from utils.get_value import get_value
from utils.format import Format
from rich.columns import Columns


def cli_pve(_configs, _data, _richs, _layout):
    if _data['pve_enabled']:
        if get_value(_configs, 'homeassistant.pve_power_sensor_id'):
            if 'pve_power' in _data:
                _richs['pve_power'].renderable = Format.power(_data['pve_power'], True)
            else:
                _richs['pve_power'].renderable = Format.yellow('loading')

        if 'pve_cpu_count' in _data:
            _richs['pve_cpu_count'].renderable = f"{_data['pve_cpu_count']} 核"
            _richs['pve_cpu_count'].style = 'none'
        else:
            _richs['pve_cpu_count'].renderable = Format.yellow('loading')

        if 'pve_cpu_freq' in _data:
            _richs['pve_cpu_freq'].renderable = f"{_data['pve_cpu_freq']} MHz"
            _richs['pve_cpu_freq'].style = 'none'
        else:
            _richs['pve_cpu_freq'].renderable = Format.yellow('loading')

        if 'pve_cpu_usage' in _data:
            _richs['pve_cpu_usage'].renderable = Format.usage(_data['pve_cpu_usage'], True)
        else:
            _richs['pve_cpu_usage'].renderable = Format.yellow('loading')

        if 'pve_mem_total' in _data:
            _richs['pve_mem_total'].renderable = Format.size(_data['pve_mem_total'], True)
        else:
            _richs['pve_mem_total'].renderable = Format.yellow('loading')

        if 'pve_mem_usage' in _data:
            _richs['pve_mem_usage'].renderable = Format.size(_data['pve_mem_usage'], True)
        else:
            _richs['pve_mem_usage'].renderable = Format.yellow('loading')

        if 'pve_cpu_fan_value' in _data:
            _richs['pve_cpu_fan_value'].renderable = f"{_data['pve_cpu_fan_value']} RPM"
            _richs['pve_cpu_fan_value'].style = 'none'
        else:
            _richs['pve_cpu_fan_value'].renderable = Format.yellow('loading')

        if 'pve_disk_fan_value' in _data:
            _richs['pve_disk_fan_value'].renderable = f"{_data['pve_disk_fan_value']} RPM"
            _richs['pve_disk_fan_value'].style = 'none'
        else:
            _richs['pve_disk_fan_value'].renderable = Format.yellow('loading')

        if 'pve_cpu_temp_value' in _data:
            _richs['pve_cpu_temp_value'].renderable = Format.temp(_data['pve_cpu_temp_value'], True)
        else:
            _richs['pve_cpu_temp_value'].renderable = Format.yellow('loading')

        if 'pve_nvme_temp_value' in _data:
            _richs['pve_nvme_temp_value'].renderable = Format.temp(_data['pve_nvme_temp_value'], True)
        else:
            _richs['pve_nvme_temp_value'].renderable = Format.yellow('loading')

        renderables = []
        if get_value(_configs, 'homeassistant.pve_power_sensor_id'):
            renderables.append(_richs['pve_power'])
        renderables += [
            _richs['pve_cpu_count'],
            _richs['pve_cpu_freq'],
            _richs['pve_cpu_usage'],
            _richs['pve_mem_total'],
            _richs['pve_mem_usage'],
            _richs['pve_cpu_fan_value'],
            _richs['pve_disk_fan_value'],
            _richs['pve_cpu_temp_value'],
            _richs['pve_nvme_temp_value'],
        ]
        pve_columns = Columns(renderables, title="ProxmoxVE", expand=True)
        _layout["ProxmoxVE"].update(pve_columns)
