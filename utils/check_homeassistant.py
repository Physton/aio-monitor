import traceback
from utils.get_value import get_value
import requests


def check_homeassistant(_configs, _data, _log):
    address = get_value(_configs, 'homeassistant.address', None)
    token = get_value(_configs, 'homeassistant.token', None)
    sensors = get_value(_configs, 'homeassistant.sensors', [])
    success = False
    if address and token:
        if sensors and len(sensors) > 0:
            _data['homeassistant_enabled'] = True
        try:
            url = f'{address}/api/states'
            headers = {'Authorization': f'Bearer {token}'}
            r = requests.get(url, headers=headers)
            r.close()
            data = r.json()
            for item in data:
                for sensor in sensors:
                    if sensor['id'] == item['entity_id']:
                        sensor['value'] = item['state']
                        sensor['unit'] = get_value(item, 'attributes.unit_of_measurement', '')
                        sensor['unit'] = '' if not sensor['unit'] else sensor['unit']
                        break

                if get_value(_configs, 'homeassistant.pve_power_sensor_id') and item['entity_id'] == get_value(_configs, 'homeassistant.pve_power_sensor_id'):
                    _data['pve_power'] = float(item['state'])
                    _data['pve_power_unit'] = get_value(item, 'attributes.unit_of_measurement', '')
                    _data['pve_power_unit'] = '' if not _data['pve_power_unit'] else _data['pve_power_unit']

            _data['homeassistant'] = sensors
            success = True
        except Exception as e:
            _log.write(f'_check_homeassistant {str(e)}')
            _log.write(traceback.format_exc())
    if not success:
        _data['pve_power'] = 'N/A'
        _data['pve_power_unit'] = 'N/A'
