from typing import Optional
import traceback
from utils.get_value import get_value
from utils.ssh_exec_command import ssh_exec_command
from paramiko import SSHClient
import paramiko
import json

ssh: Optional[SSHClient] = None


def check_pve_ssh(_configs, _data, _log):
    global ssh
    pve_host = get_value(_configs, 'pve_ssh.host', None)
    pve_port = get_value(_configs, 'pve_ssh.port', None)
    pve_username = get_value(_configs, 'pve_ssh.username', None)
    pve_password = get_value(_configs, 'pve_ssh.password', None)
    disk_fan = get_value(_configs, 'pve_ssh.disk_fan', None)
    cpu_fan = get_value(_configs, 'pve_ssh.cpu_fan', None)
    cpu_temp = get_value(_configs, 'pve_ssh.cpu_temp', None)
    nvme_temp = get_value(_configs, 'pve_ssh.nvme_temp', None)
    sensors_success = False
    cpuinfo_success = False
    if pve_host and pve_port and pve_username and pve_password:
        _data['pve_enabled'] = True
        try:
            if not ssh:
                ssh = paramiko.SSHClient()
                # 允许自动接受未知的主机密钥（在生产环境中应谨慎使用）
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(pve_host, port=pve_port, username=pve_username, password=pve_password,
                            timeout=5)

            if not ssh.get_transport().is_active():
                ssh = None
                raise Exception('SSH is not active')

            try:
                stdout_result = ssh_exec_command(ssh, 'sensors -j')
                sensors = json.loads(stdout_result)
                # _configs['pve']['sensors'] = sensors
                _data['pve_disk_fan_value'] = get_value(sensors, disk_fan)
                _data['pve_cpu_fan_value'] = get_value(sensors, cpu_fan)
                _data['pve_cpu_temp_value'] = get_value(sensors, cpu_temp)
                _data['pve_nvme_temp_value'] = get_value(sensors, nvme_temp)
                sensors_success = True
            except Exception as e:
                _log.write(f'_check_pve_ssh sensors {str(e)}')
                _log.write(traceback.format_exc())

            try:
                stdout_result = ssh_exec_command(ssh, "cat /proc/cpuinfo | grep 'MHz'")
                cpufreqs = []
                for line in stdout_result.split('\n'):
                    if line:
                        cpufreqs.append(float(line.split(':')[1].strip()))
                _data['pve_cpu_freq'] = round(sum(cpufreqs) / len(cpufreqs), 3)
                cpuinfo_success = True
            except Exception as e:
                _log.write(f'_check_pve_ssh cpuinfo {str(e)}')
                _log.write(traceback.format_exc())
        except Exception as e:
            ssh = None
            _log.write(f'_check_pve_ssh {str(e)}')
            _log.write(traceback.format_exc())
            pass

    if not sensors_success:
        _data['pve_disk_fan_value'] = 'N/A'
        _data['pve_cpu_fan_value'] = 'N/A'
        _data['pve_cpu_temp_value'] = 'N/A'
        _data['pve_nvme_temp_value'] = 'N/A'
    if not cpuinfo_success:
        _data['pve_cpu_freq'] = 'N/A'


def close_pve_ssh():
    global ssh
    if ssh:
        ssh.close()
