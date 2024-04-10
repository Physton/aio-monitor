from typing import Optional
import traceback
from utils.get_value import get_value
import synology_api
from synology_api.core_sys_info import SysInfo

api: Optional[SysInfo] = None


def check_nas_disk(_configs, _data, _log):
    global api
    dsm_host = get_value(_configs, 'dsm.host', None)
    dsm_port = get_value(_configs, 'dsm.port', None)
    dsm_username = get_value(_configs, 'dsm.username', None)
    dsm_password = get_value(_configs, 'dsm.password', None)

    dsm_success = False
    if dsm_host and dsm_port and dsm_username and dsm_password:
        _data['dsm_enabled'] = True
        try:
            if not api:
                api = synology_api.core_sys_info.SysInfo(ip_address=dsm_host,
                                                         port=dsm_port,
                                                         username=dsm_username,
                                                         password=dsm_password,
                                                         secure=False, cert_verify=False, dsm_version=7,
                                                         debug=False,
                                                         otp_code=None)

            dsm_storage = api.storage()
            dsm_disk_utilization = api.get_disk_utilization()
            dsm_success = True

            if dsm_storage and dsm_disk_utilization:
                for disk in get_value(dsm_storage, 'data.disks', []):
                    utilization = None
                    for disk_utilization in get_value(dsm_disk_utilization, 'disk', []):
                        if disk_utilization['device'] == disk['id']:
                            utilization = disk_utilization
                            break
                    disk['utilization'] = None if not utilization else utilization

            _data['dsm_storage'] = dsm_storage
            _data['dsm_disk_utilization'] = dsm_disk_utilization

        except Exception as e:
            api = None
            _log.write(f'_check_nas_disk {str(e)}')
            _log.write(traceback.format_exc())

    # if not dsm_success:
    #     _data['dsm_storage'] = None
    #     _data['dsm_disk_utilization'] = None
