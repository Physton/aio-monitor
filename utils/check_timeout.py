import subprocess
import re
from utils.get_value import get_value


def check_timeout(_configs, _data, _log, address):
    try:
        result = subprocess.run(f'ping -c 1 {address}', shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        if result.returncode == 0:
            stdout = result.stdout.decode().strip()
            if 'timeout' in stdout:
                raise Exception('timeout')
            elif 'time=' in stdout:
                time_match = re.search(r'time=([0-9\.]+)\s*ms', stdout)
                if time_match:
                    timeout = float(time_match.group(1))
                    _set_address_timeout(_configs, _data, _log, address, timeout)
                    return timeout
                else:
                    raise Exception('unknown output')
            else:
                raise Exception('unknown output')
        else:
            raise Exception('ping error')
    except Exception as e:
        _log.write(f'_check_timeout {address} {str(e)}')
        _set_address_timeout(_configs, _data, _log, address, None)


def _set_address_timeout(_configs, _data, _log, address, timeout):
    for item in get_value(_configs, 'addresses', []):
        if item['local'] == address:
            item['local_timeout'] = timeout
        if item['public'] == address:
            item['public_timeout'] = timeout
