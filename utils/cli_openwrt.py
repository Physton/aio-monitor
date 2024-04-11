from utils.get_value import get_value
from utils.format import Format
from rich.columns import Columns


def cli_openwrt(_configs, _data, _richs, _layout):
    if _data['openwrt_enabled']:
        if 'op_cpu_temp_value' in _data:
            _richs['op_cpu_temp_value'].renderable = Format.temp(_data['op_cpu_temp_value'], True)
        else:
            _richs['op_cpu_temp_value'].renderable = Format.yellow('loading')

        if 'op_cpu_count' in _data:
            _richs['op_cpu_count'].renderable = f"{_data['op_cpu_count']} 核"
            _richs['op_cpu_count'].style = 'none'
        else:
            _richs['op_cpu_count'].renderable = Format.yellow('loading')

        if 'op_cpu_freq' in _data:
            _richs['op_cpu_freq'].renderable = f"{_data['op_cpu_freq']} MHz"
            _richs['op_cpu_freq'].style = 'none'
        else:
            _richs['op_cpu_freq'].renderable = Format.yellow('loading')

        if 'op_cpu_usage' in _data:
            _richs['op_cpu_usage'].renderable = Format.usage(_data['op_cpu_usage'], True)
        else:
            _richs['op_cpu_usage'].renderable = Format.yellow('loading')

        if 'op_uptime_str' in _data:
            _richs['op_uptime'].renderable = _data['op_uptime_str']
            _richs['op_uptime'].style = 'none'
        else:
            _richs['op_uptime'].renderable = Format.yellow('loading')

        if 'op_mem_total' in _data:
            _richs['op_mem_total'].renderable = Format.size(_data['op_mem_total'], True)
        else:
            _richs['op_mem_total'].renderable = Format.yellow('loading')

        if 'op_mem_usage' in _data:
            _richs['op_mem_usage'].renderable = Format.size(_data['op_mem_usage'], True)
        else:
            _richs['op_mem_usage'].renderable = Format.yellow('loading')

        if 'op_client_num' in _data:
            _richs['op_client_num'].renderable = str(_data['op_client_num'])
            _richs['op_client_num'].style = 'none'
        else:
            _richs['op_client_num'].renderable = Format.yellow('loading')

        if 'op_connect_num' in _data:
            _richs['op_connect_num'].renderable = str(_data['op_connect_num'])
            _richs['op_connect_num'].style = 'none'
        else:
            _richs['op_connect_num'].renderable = Format.yellow('loading')

        if 'op_totaldown' in _data:
            _richs['op_totaldown'].renderable = Format.size(_data['op_totaldown'], True)
        else:
            _richs['op_totaldown'].renderable = Format.yellow('loading')

        if 'op_totalup' in _data:
            _richs['op_totalup'].renderable = Format.size(_data['op_totalup'], True)
        else:
            _richs['op_totalup'].renderable = Format.yellow('loading')

        if 'op_download' in _data:
            _richs['op_download'].renderable = Format.size_flow(_data['op_download'], True)
        else:
            _richs['op_download'].renderable = Format.yellow('loading')

        if 'op_upload' in _data:
            _richs['op_upload'].renderable = Format.size_flow(_data['op_upload'], True)
        else:
            _richs['op_upload'].renderable = Format.yellow('loading')

        _layout["OpenWrt"].update(Columns([
            _richs['op_uptime'],
            _richs['op_cpu_count'],
            _richs['op_cpu_freq'],
            _richs['op_cpu_usage'],
            _richs['op_cpu_temp_value'],
            _richs['op_mem_total'],
            _richs['op_mem_usage'],
            _richs['op_client_num'],
            _richs['op_connect_num'],
            _richs['op_totaldown'],
            _richs['op_totalup'],
            _richs['op_download'],
            _richs['op_upload'],
        ], title="OpenWrt", expand=True))
