from typing import Optional
import traceback
from utils.get_value import get_value
from proxmoxer import ProxmoxAPI

api: Optional[ProxmoxAPI] = None


def check_pve_web(_configs, _data, _log):
    global api
    pve_host = get_value(_configs, 'pve_web.host', None)
    pve_port = get_value(_configs, 'pve_web.port', None)
    pve_username = get_value(_configs, 'pve_web.username', None)
    pve_password = get_value(_configs, 'pve_web.password', None)
    node_success = False
    qemus_success = False
    if pve_host and pve_port and pve_username and pve_password:
        _data['pve_enabled'] = True
        try:
            if not api:
                api = ProxmoxAPI(pve_host, port=pve_port, user=pve_username, password=pve_password, verify_ssl=False)
            response = api.cluster().resources().get()
            qemus = []
            for item in response:
                if item['type'] == 'node':
                    _data['pve_cpu_usage'] = item['cpu']
                    _data['pve_cpu_count'] = item['maxcpu']
                    _data['pve_mem_usage'] = item['mem']
                    _data['pve_mem_total'] = item['maxmem']
                    _data['pve_disk_usage'] = item['disk']
                    _data['pve_disk_total'] = item['maxdisk']
                    node_success = True
                elif item['type'] == 'qemu' or item['type'] == 'lxc':
                    qemus.append(item)
                    qemus_success = True
            _data['pve_qemus'] = qemus
        except Exception as e:
            api = None
            _log.write(f'_check_pve_web {str(e)}')
            _log.write(traceback.format_exc())

    if not node_success:
        _data['pve_cpu_usage'] = 'N/A'
        _data['pve_cpu_count'] = 'N/A'
        _data['pve_mem_usage'] = 'N/A'
        _data['pve_mem_total'] = 'N/A'
        _data['pve_disk_usage'] = 'N/A'
        _data['pve_disk_total'] = 'N/A'
    if not qemus_success:
        _data['pve_qemus'] = []
