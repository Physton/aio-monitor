from utils.get_value import get_value
from utils.format import Format
from rich.columns import Columns


def cli_homeassistant(_configs, _data, _richs, _layout):
    if _data['homeassistant_enabled']:
        temp_richs = []
        for sensor in get_value(_configs, 'homeassistant.sensors', []):
            rich_key = f"ha.{sensor['id']}"
            find = False
            find_item = {}

            for item in get_value(_data, 'homeassistant', []):
                if item['id'] == sensor['id']:
                    find = True
                    find_item = item
                    break
            if find:
                value = str(find_item['value'])
                if find_item['unit']:
                    value += f"{find_item['unit']}"
                _richs[rich_key].renderable = value
            else:
                _richs[rich_key].renderable = Format.yellow('loading')
            temp_richs.append(_richs[rich_key])
        if len(temp_richs):
            ha_columns = Columns(temp_richs, title="HomeAssistant", expand=True)
            _layout["HomeAssistant"].update(ha_columns)
