from typing import Optional
import traceback
from utils.get_value import get_value
from utils.ssh_exec_command import ssh_exec_command
from utils.is_subnet import is_subnet
from utils.format import Format
from paramiko import SSHClient
import paramiko
import json
import ipaddress

ssh: Optional[SSHClient] = None


def check_op_ssh(_configs, _data, _log):
    global ssh
    op_host = get_value(_configs, 'op_ssh.host', None)
    op_port = get_value(_configs, 'op_ssh.port', None)
    op_username = get_value(_configs, 'op_ssh.username', None)
    op_password = get_value(_configs, 'op_ssh.password', None)
    cpu_temp = get_value(_configs, 'op_ssh.cpu_temp', None)
    sensors_success = False
    cpuinfo_success = False
    mpstat_success = False
    ubus_success = False
    if op_host and op_port and op_username and op_password:
        _data['openwrt_enabled'] = True
        try:
            if not ssh:
                ssh = paramiko.SSHClient()
                # 允许自动接受未知的主机密钥（在生产环境中应谨慎使用）
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(op_host, port=op_port, username=op_username, password=op_password, timeout=5)

            if not ssh.get_transport().is_active():
                ssh = None
                raise Exception('SSH is not active')

            try:
                stdout_result = ssh_exec_command(ssh, 'sensors -j')
                sensors = json.loads(stdout_result)
                _data['op_cpu_temp_value'] = get_value(sensors, cpu_temp)
                sensors_success = True
            except Exception as e:
                _log.write(f'_check_op_ssh sensors {str(e)}')
                _log.write(traceback.format_exc())

            try:
                stdout_result = ssh_exec_command(ssh, "cat /proc/cpuinfo | grep 'MHz'")
                cpufreqs = []
                for line in stdout_result.split('\n'):
                    if line:
                        cpufreqs.append(float(line.split(':')[1].strip()))
                _data['op_cpu_freq'] = round(sum(cpufreqs) / len(cpufreqs), 3)
                _data['op_cpu_count'] = len(cpufreqs)
                cpuinfo_success = True
            except Exception as e:
                _log.write(f'_check_op_ssh cpuinfo {str(e)}')
                _log.write(traceback.format_exc())

            try:
                stdout_result = ssh_exec_command(ssh, "mpstat -P all 1 1 | grep 'all' | awk 'NR==1{print $12}'")
                _data['op_cpu_usage'] = (100 - float(stdout_result)) / 100
                mpstat_success = True
            except Exception as e:
                _log.write(f'_check_op_ssh mpstat {str(e)}')
                _log.write(traceback.format_exc())

            try:
                stdout_result = ssh_exec_command(ssh, "ubus call system info")
                info = json.loads(stdout_result)
                _data['op_uptime'] = info['uptime']
                _data['op_uptime_str'] = Format.uptime(_data['op_uptime'])
                _data['op_mem_total'] = info['memory']['total']
                _data['op_mem_usage'] = info['memory']['total'] - info['memory']['free']

                # stdout_result = ssh_exec_command(ssh, "ubus call luci getConntrackList")
                # info = json.loads(stdout_result)
                # _data['op_connect_num'] = info['count']
                params = json.dumps({'mode': 'conntrack'})
                stdout_result = ssh_exec_command(ssh, f"ubus call luci getRealtimeStats '{params}'")
                info = json.loads(stdout_result)
                last_item = info['result'][-1]
                _data['op_connect_num_tcp'] = last_item[1]
                _data['op_connect_num_udp'] = last_item[2]
                _data['op_connect_num_other'] = last_item[3]
                _data['op_connect_num'] = last_item[1] + last_item[2] + last_item[3]

                stdout_result = ssh_exec_command(ssh, "ubus call network.interface.wan status")
                info = json.loads(stdout_result)
                _data['op_wan_device'] = info['device']
                params = json.dumps({
                    'mode': 'interface',
                    'device': info['device']
                })
                stdout_result = ssh_exec_command(ssh, f"ubus call luci getRealtimeStats '{params}'")
                info = json.loads(stdout_result)
                last_item = info['result'][-1]
                prev_item = info['result'][-2]
                _data['op_totaldown'] = last_item[1]
                _data['op_totalup'] = last_item[3]
                _data['op_download'] = last_item[1] - prev_item[1]
                _data['op_upload'] = last_item[3] - prev_item[3]

                stdout_result = ssh_exec_command(ssh, "ubus call network.interface.lan status")
                info = json.loads(stdout_result)
                addresses = []
                subnets = []
                for item in info['ipv4-address']:
                    ip_iface = ipaddress.ip_interface(f'{item["address"]}/{item["mask"]}')
                    ip_subnet = f"{ip_iface.network.network_address}/{ip_iface.network.prefixlen}"
                    addresses.append(item["address"])
                    subnets.append(ip_subnet)

                stdout_result = ssh_exec_command(ssh, "ubus call luci-rpc getHostHints")
                info = json.loads(stdout_result)
                _data['op_client_num'] = 0
                for key in info:
                    item = info[key]
                    if len(item['ipaddrs']) == 0:
                        continue
                    for ipaddr in item['ipaddrs']:
                        if ipaddr in addresses:
                            break
                        if is_subnet(ipaddr, subnets):
                            _data['op_client_num'] += 1
                            break

                ubus_success = True
            except Exception as e:
                _log.write(f'_check_op_ssh ubus {str(e)}')
                _log.write(traceback.format_exc())

        except Exception as e:
            ssh = None
            _log.write(f'_check_op_ssh {str(e)}')
            _log.write(traceback.format_exc())
            pass

    if not sensors_success:
        _data['op_cpu_temp_value'] = 'N/A'
    if not cpuinfo_success:
        _data['op_cpu_freq'] = 'N/A'
        _data['op_cpu_count'] = 'N/A'
    if not mpstat_success:
        _data['op_cpu_usage'] = 'N/A'
    if not ubus_success:
        _data['op_uptime'] = 'N/A'
        _data['op_uptime_str'] = 'N/A'
        _data['op_mem_total'] = 'N/A'
        _data['op_mem_usage'] = 'N/A'
        _data['op_connect_num_tcp'] = 'N/A'
        _data['op_connect_num_udp'] = 'N/A'
        _data['op_connect_num_other'] = 'N/A'
        _data['op_connect_num'] = 'N/A'
        _data['op_wan_device'] = 'N/A'
        _data['op_totaldown'] = 'N/A'
        _data['op_totalup'] = 'N/A'
        _data['op_download'] = 'N/A'
        _data['op_upload'] = 'N/A'
        _data['op_client_num'] = 'N/A'


def close_op_ssh():
    global ssh
    if ssh:
        ssh.close()
