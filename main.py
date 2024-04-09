import os
import sys
import json
import time
import synology_api
import socket
import threading
import signal
import subprocess
import re
import yaml
import requests
import paramiko
import argparse
import hashlib
import netifaces
from proxmoxer import ProxmoxAPI
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from uvicorn import Server
from uvicorn import Config as uvicornConfig
from rich.console import Console
from rich.live import Live
from rich.columns import Columns
from rich.panel import Panel
from rich.panel import Style
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
import rich.box as Box
import warnings
import urllib3.exceptions

warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

__title__ = 'All-in-one Monitor'
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.txt'), 'r') as f:
    __version__ = f.read().strip()

class Main:
    web_gui = True
    shell_gui = True
    config_file = None
    logs_path = None
    configs = {}
    addresses = []
    threads = []
    is_stop = False
    data = {}
    app = None
    server = None

    console = Console()

    color_yellow = "bright_yellow"
    color_red = "bright_red"
    color_blue = "bright_blue"
    color_purple = "purple"
    color_green = "bright_green"

    def __init__(self, web_gui=True, shell_gui=True, config_file=None, logs_path=None):
        self.web_gui = web_gui
        self.shell_gui = shell_gui
        if not config_file:
            self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        else:
            self.config_file = config_file
        if not os.path.isfile(self.config_file):
            print(f'\033[1;31mconfig file not found: {self.config_file}\033[0m')
            sys.exit(1)
        if not logs_path:
            self.logs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        else:
            self.logs_path = logs_path

        if not os.path.isdir(self.logs_path):
            print(f'\033[1;31mlogs path not found: {self.logs_path}\033[0m')
            sys.exit(1)

        try:
            self.configs = yaml.load(open(self.config_file), Loader=yaml.FullLoader)
            self.data['app_background_image'] = self.get_value(self.configs, 'app_background_image', '')
            self.data['app_background_blur'] = self.get_value(self.configs, 'app_background_blur', 0)
            self.data['app_card_background_color'] = self.get_value(self.configs, 'app_card_background_color',
                                                                    'rgba(64, 75, 105, 1)')
        except Exception as e:
            print(f'\033[1;31mconfig file error: {str(e)}\033[0m')
            sys.exit(1)

        self._parse_addresses()
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signal, frame):
        self.is_stop = True
        if self.server:
            self.server.handle_exit(signal, frame)

    def _clear_logs(self, max_num=3):
        files = os.listdir(self.logs_path)
        if len(files) > max_num:
            for file in files[:-max_num]:
                os.remove(os.path.join(self.logs_path, file))

    def _get_log_file(self):
        file = os.path.join(self.logs_path, f'{time.strftime("%Y%m%d%H")}.log')
        if not os.path.exists(file):
            open(file, 'w').close()
            self._clear_logs()
        return file

    def _write_log(self, log):
        log = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {log}\n'
        file = self._get_log_file()
        with open(file, 'a') as f:
            f.write(log)

    def _parse_addresses(self):
        self.addresses = []
        for address in self.get_value(self.configs, 'addresses', []):
            if address['local'] not in self.addresses:
                self.addresses.append(address['local'])
            if address['public'] not in self.addresses:
                self.addresses.append(address['public'])

    def _web(self):
        app_host = self.get_value(self.configs, 'app_host', '0.0.0.0')
        app_port = self.get_value(self.configs, 'app_port', '8000')
        app_secret = self.get_value(self.configs, 'app_secret', None)
        app_expire = self.get_value(self.configs, 'app_expire', None)
        app_username = self.get_value(self.configs, 'app_username', None)
        app_password = self.get_value(self.configs, 'app_password', None)
        password_md5 = ''
        if app_password:
            password_md5 = hashlib.md5(str(app_password).encode('utf-8')).hexdigest()
            password_md5 = hashlib.md5(password_md5.encode('utf-8')).hexdigest()
        if not self.app:
            try:
                self.app = FastAPI()

                if app_username and app_password:
                    class User(BaseModel):
                        username: str
                        password: str

                    class Settings(BaseModel):
                        authjwt_secret_key: str = app_secret

                    @AuthJWT.load_config
                    def get_config():
                        return Settings()

                    @self.app.exception_handler(AuthJWTException)
                    def authjwt_exception_handler(request: Request, exc: AuthJWTException):
                        return JSONResponse(
                            status_code=exc.status_code,
                            content={"detail": exc.message}
                        )

                    @self.app.post('/api/login')
                    def login(user: User, Authorize: AuthJWT = Depends()):
                        if user.username != str(app_username) or user.password != password_md5:
                            raise HTTPException(status_code=401, detail="Bad username or password")
                        expires_time = app_expire
                        access_token = Authorize.create_access_token(
                            subject=hashlib.md5(f'{user.username}.{password_md5}'.encode('utf-8')).hexdigest(),
                            expires_time=expires_time)
                        return {"access_token": access_token}

                    @self.app.get("/api/data")
                    def api_data(Authorize: AuthJWT = Depends()):
                        if app_username and app_password:
                            Authorize.jwt_required()
                            subject = Authorize.get_jwt_subject()
                            if subject != hashlib.md5(f'{app_username}.{password_md5}'.encode('utf-8')).hexdigest():
                                raise HTTPException(status_code=401, detail="Unauthorized")
                        self.data['addresses'] = self.configs['addresses']
                        return {"data": self.data}
                else:
                    @self.app.get("/api/data")
                    def api_data():
                        self.data['addresses'] = self.configs['addresses']
                        return {"data": self.data}

                self.app.mount("/", StaticFiles(directory="./html", html=True), name="static")

                ipv4s = self._get_all_ipv4()
                for ipv4 in ipv4s:
                    print(f'Web: http://{ipv4}:{app_port}')
                print("")

                log_level = 'error' if self.shell_gui else 'info'
                config = uvicornConfig(self.app, host=app_host, port=int(app_port), log_level=log_level)
                self.server = Server(config)
                self.server.run()
            except Exception as e:
                self._write_log(f'_web {str(e)}')

    def _get_all_ipv4(self):
        ips = []
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                ips.extend([addr['addr'] for addr in addrs[netifaces.AF_INET]])
        return ips

    def _shell(self):
        richs = {}

        for sensor in self.get_value(self.configs, 'homeassistant.sensors', []):
            richs[f"ha.{sensor['id']}"] = Panel("", title=f"[b]{sensor['title']}[/b]", box=Box.SIMPLE)

        if self.get_value(self.configs, 'homeassistant.pve_power_sensor_id', []):
            richs['pve_power'] = Panel("", title='[b]整机功耗[/b]', box=Box.SIMPLE)
        richs['pve_cpu_count'] = Panel("", title='[b]CPU核心[/b]', box=Box.SIMPLE)
        richs['pve_cpu_freq'] = Panel("", title='[b]CPU频率[/b]', box=Box.SIMPLE)
        richs['pve_cpu_usage'] = Panel("", title='[b]CPU占用[/b]', box=Box.SIMPLE)
        richs['pve_mem_total'] = Panel("", title='[b]内存总量[/b]', box=Box.SIMPLE)
        richs['pve_mem_usage'] = Panel("", title='[b]内存占用[/b]', box=Box.SIMPLE)
        richs['pve_cpu_fan_value'] = Panel("", title='[b]CPU风扇[/b]', box=Box.SIMPLE)
        richs['pve_disk_fan_value'] = Panel("", title='[b]硬盘风扇[/b]', box=Box.SIMPLE)
        richs['pve_cpu_temp_value'] = Panel("", title='[b]CPU温度[/b]', box=Box.SIMPLE)
        richs['pve_nvme_temp_value'] = Panel("", title='[b]M2温度[/b]', box=Box.SIMPLE)

        layouts = []
        if self.get_value(self.configs, 'homeassistant.sensors', []):
            layouts.append(Layout(name="HomeAssistant", size=4))
        layouts.append(Layout(name="ProxmoxVE", size=4))
        layouts.append(Layout(name="ServiceList"))
        layouts.append(Layout(name="QemuList"))
        layouts.append(Layout(name="DiskList"))
        layout = Layout(name="root")
        layout.split_column(*layouts)

        with Live(layout, refresh_per_second=1, screen=True) as live:
            while not self.is_stop:
                # live.console.clear()

                temp_richs = []
                for sensor in self.get_value(self.configs, 'homeassistant.sensors', []):
                    rich_key = f"ha.{sensor['id']}"
                    find = False

                    for item in self.get_value(self.data, 'homeassistant', []):
                        if item['id'] == sensor['id']:
                            find = item
                            break
                    if find:
                        value = str(find['value'])
                        if find['unit']:
                            value += f"{find['unit']}"
                        richs[rich_key].renderable = value
                    else:
                        richs[rich_key].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'
                    temp_richs.append(richs[rich_key])
                if len(temp_richs):
                    ha_columns = Columns(temp_richs, title="HomeAssistant", expand=True)
                    layout["HomeAssistant"].update(ha_columns)

                if self.get_value(self.configs, 'homeassistant.pve_power_sensor_id'):
                    if 'pve_power' in self.data:
                        richs['pve_power'].renderable = self.format_power(self.data['pve_power'], True)
                    else:
                        richs['pve_power'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_cpu_count' in self.data:
                    richs['pve_cpu_count'].renderable = f"{self.data['pve_cpu_count']} 核"
                    richs['pve_cpu_count'].style = 'none'
                else:
                    richs['pve_cpu_count'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_cpu_freq' in self.data:
                    richs['pve_cpu_freq'].renderable = f"{self.data['pve_cpu_freq']} MHz"
                    richs['pve_cpu_freq'].style = 'none'
                else:
                    richs['pve_cpu_freq'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_cpu_usage' in self.data:
                    richs['pve_cpu_usage'].renderable = self.format_usage(self.data['pve_cpu_usage'], True)
                else:
                    richs['pve_cpu_usage'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_mem_total' in self.data:
                    richs['pve_mem_total'].renderable = self.format_size(self.data['pve_mem_total'], True)
                else:
                    richs['pve_mem_total'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_mem_usage' in self.data:
                    richs['pve_mem_usage'].renderable = self.format_size(self.data['pve_mem_usage'], True)
                else:
                    richs['pve_mem_usage'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_cpu_fan_value' in self.data:
                    richs['pve_cpu_fan_value'].renderable = f"{self.data['pve_cpu_fan_value']} RPM"
                    richs['pve_cpu_fan_value'].style = 'none'
                else:
                    richs['pve_cpu_fan_value'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_disk_fan_value' in self.data:
                    richs['pve_disk_fan_value'].renderable = f"{self.data['pve_disk_fan_value']} RPM"
                    richs['pve_disk_fan_value'].style = 'none'
                else:
                    richs['pve_disk_fan_value'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_cpu_temp_value' in self.data:
                    richs['pve_cpu_temp_value'].renderable = self.format_temp(self.data['pve_cpu_temp_value'], True)
                else:
                    richs['pve_cpu_temp_value'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                if 'pve_nvme_temp_value' in self.data:
                    richs['pve_nvme_temp_value'].renderable = self.format_temp(self.data['pve_nvme_temp_value'], True)
                else:
                    richs['pve_nvme_temp_value'].renderable = f'[{self.color_yellow}]loading[/{self.color_yellow}]'

                renderables = []
                if self.get_value(self.configs, 'homeassistant.pve_power_sensor_id'):
                    renderables.append(richs['pve_power'])
                renderables += [
                    richs['pve_cpu_count'],
                    richs['pve_cpu_freq'],
                    richs['pve_cpu_usage'],
                    richs['pve_mem_total'],
                    richs['pve_mem_usage'],
                    richs['pve_cpu_fan_value'],
                    richs['pve_disk_fan_value'],
                    richs['pve_cpu_temp_value'],
                    richs['pve_nvme_temp_value'],
                ]
                pve_columns = Columns(renderables, title="ProxmoxVE", expand=True)
                layout["ProxmoxVE"].update(pve_columns)

                server_table = Table(show_header=True, header_style="bold", box=Box.SIMPLE, expand=True)
                server_table.add_column("服务列表", justify="center", no_wrap=True)
                server_table.add_column("本地", justify="left", no_wrap=True)
                server_table.add_column("本地延迟", justify="right", no_wrap=True)
                server_table.add_column("本地端口", justify="right", no_wrap=True)
                server_table.add_column("公网", justify="left", no_wrap=True)
                server_table.add_column("公网延迟", justify="right", no_wrap=True)
                server_table.add_column("公网端口", justify="right", no_wrap=True)
                for address in self.get_value(self.configs, 'addresses', []):
                    server_table.add_row(
                        address['name'],
                        f"{address['local']}:{address['local_port']}",
                        self.format_timeout(address, 'local_timeout'),
                        self.format_port(address, 'local_port_status'),
                        # f"{address['public']}:{address['public_port']}",
                        f"{address['public_port']}",
                        self.format_timeout(address, 'public_timeout'),
                        self.format_port(address, 'public_port_status'),
                    )
                layout["ServiceList"].update(server_table)

                pve_qemus_table = Table(show_header=True, header_style="bold", box=Box.SIMPLE, expand=True)
                pve_qemus_table.add_column("PVE虚拟机状态", justify="center", no_wrap=True)
                pve_qemus_table.add_column("ID", justify="center", no_wrap=True)
                pve_qemus_table.add_column("名称", justify="left", no_wrap=True)
                pve_qemus_table.add_column("类型", justify="center", no_wrap=True)
                pve_qemus_table.add_column("CPU核心", justify="center", no_wrap=True)
                pve_qemus_table.add_column("CPU占用", justify="right", no_wrap=True)
                pve_qemus_table.add_column("内存总量", justify="right", no_wrap=True)
                pve_qemus_table.add_column("内存占用", justify="right", no_wrap=True)
                pve_qemus_table.add_column("流入流量", justify="right", no_wrap=True)
                pve_qemus_table.add_column("流出流量", justify="right", no_wrap=True)
                for qemu in self.get_value(self.data, 'pve_qemus', []):
                    pve_qemus_table.add_row(
                        '[bright_green]running[/bright_green]' if qemu[
                                                                      'status'] == 'running' else f"[bright_red]{qemu['status']}[/bright_red]",
                        str(qemu['vmid']),
                        qemu['name'],
                        qemu['type'],
                        f"{qemu['maxcpu']} 核",
                        self.format_usage(qemu['cpu'], True),
                        self.format_size(qemu['maxmem'], True),
                        self.format_size(qemu['mem'], True),
                        self.format_size(qemu['netin'], True),
                        self.format_size(qemu['netout'], True),
                    )
                layout["QemuList"].update(pve_qemus_table)

                disks_table = Table(show_header=True, header_style="bold", box=Box.SIMPLE, expand=True)
                disks_table.add_column("NAS存储", justify="center", no_wrap=True)
                disks_table.add_column("型号", justify="left", no_wrap=True)
                disks_table.add_column("序列号", justify="left", no_wrap=True)
                disks_table.add_column("容量", justify="right", no_wrap=True)
                disks_table.add_column("温度", justify="right", no_wrap=True)
                disks_table.add_column("读取", justify="right", no_wrap=True)
                disks_table.add_column("写入", justify="right", no_wrap=True)
                for disk in self.get_value(self.data, 'dsm_storage.data.disks', []):
                    disks_table.add_row(
                        disk['id'],
                        disk['model'],
                        disk['serial'],
                        self.format_size(disk['size_total'], True),
                        self.format_hdd_temp(disk['temp'], True) if disk[
                                                                        'diskType'] == 'SATA' else self.format_temp(
                            disk['temp'], True),
                        self.format_size(disk['utilization']['read_byte'],
                                         True) if disk['utilization'] else '[bright_yellow]loading[/bright_yellow]',
                        self.format_size(disk['utilization']['write_byte'],
                                         True) if disk['utilization'] else '[bright_yellow]loading[/bright_yellow]',
                    )
                layout["DiskList"].update(disks_table)

                # live.console.print(ha_columns)
                # live.console.print(pve_columns)
                # live.console.print(server_table)
                # live.console.print(pve_qemus_table)
                # live.console.print(disks_table)
                # live.update([pve_columns, server_table, pve_qemus_table, disks_table])
                time.sleep(1)

    def _check_timeout(self, address):
        while not self.is_stop:
            try:
                result = subprocess.run(f'ping -c 1 {address}', shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                if result.returncode == 0:
                    stdout = result.stdout.decode().strip()
                    if 'timeout' in stdout:
                        self._write_log(f'_check_timeout {address} {str(e)}')
                        self._set_address_timeout(address, None)
                    elif 'time=' in stdout:
                        time_match = re.search(r'time=([0-9\.]+)\s*ms', stdout)
                        if time_match:
                            self._set_address_timeout(address, time_match.group(1))
                    else:
                        self._write_log(f'_check_timeout {address} {str(e)}')
                        self._set_address_timeout(address, None)
                else:
                    self._set_address_timeout(address, None)
            except Exception as e:
                self._write_log(f'_check_timeout {address} {str(e)}')
                self._set_address_timeout(address, None)
            time.sleep(1)

    def _set_address_timeout(self, address, timeout):
        for item in self.get_value(self.configs, 'addresses', []):
            if item['local'] == address:
                item['local_timeout'] = timeout
            if item['public'] == address:
                item['public_timeout'] = timeout

    def _check_port(self, address, port):
        while not self.is_stop:
            try:
                # 创建一个socket对象
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # 设置超时时间为5秒
                # 尝试连接
                sock.connect((address, port))
                # 关闭连接
                sock.close()
                self._set_port_status(address, port, True)
            except (socket.timeout, ConnectionRefusedError, socket.gaierror) as e:
                self._write_log(f'_check_port {address}:{port} {str(e)}')
                self._set_port_status(address, port, False)
            except Exception as e:
                self._write_log(f'_check_port {address}:{port} {str(e)}')
                self._set_port_status(address, port, False)

            time.sleep(3)

    def _set_port_status(self, address, port, status):
        for item in self.get_value(self.configs, 'addresses', []):
            if item['local'] == address and item['local_port'] == port:
                item['local_port_status'] = status
            if item['public'] == address and item['public_port'] == port:
                item['public_port_status'] = status

    def _check_pve_web(self):
        api = None
        while not self.is_stop:
            pve_host = self.get_value(self.configs, 'pve_web.host', None)
            pve_port = self.get_value(self.configs, 'pve_web.port', None)
            pve_username = self.get_value(self.configs, 'pve_web.username', None)
            pve_password = self.get_value(self.configs, 'pve_web.password', None)
            node_success = False
            qemus_success = False
            if pve_host and pve_port and pve_username and pve_password:
                try:
                    if not api:
                        api = ProxmoxAPI(pve_host, port=pve_port, user=pve_username, password=pve_password,
                                         verify_ssl=False)
                    response = api.cluster().resources().get()
                    qemus = []
                    for item in response:
                        if item['type'] == 'node':
                            self.data['pve_cpu_usage'] = item['cpu']
                            self.data['pve_cpu_count'] = item['maxcpu']
                            self.data['pve_mem_usage'] = item['mem']
                            self.data['pve_mem_total'] = item['maxmem']
                            self.data['pve_disk_usage'] = item['disk']
                            self.data['pve_disk_total'] = item['maxdisk']
                            node_success = True
                        elif item['type'] == 'qemu' or item['type'] == 'lxc':
                            qemus.append(item)
                            qemus_success = True
                    self.data['pve_qemus'] = qemus
                except Exception as e:
                    api = None
                    self._write_log(f'_check_pve_web {str(e)}')

            if not node_success:
                self.data['pve_cpu_usage'] = 'N/A'
                self.data['pve_cpu_count'] = 'N/A'
                self.data['pve_mem_usage'] = 'N/A'
                self.data['pve_mem_total'] = 'N/A'
                self.data['pve_disk_usage'] = 'N/A'
                self.data['pve_disk_total'] = 'N/A'
            if not qemus_success:
                self.data['pve_qemus'] = []
            time.sleep(1)

    def _check_pve_ssh(self):
        ssh = None
        while not self.is_stop:
            pve_host = self.get_value(self.configs, 'pve_ssh.host', None)
            pve_port = self.get_value(self.configs, 'pve_ssh.port', None)
            pve_username = self.get_value(self.configs, 'pve_ssh.username', None)
            pve_password = self.get_value(self.configs, 'pve_ssh.password', None)
            disk_fan = self.configs['pve_ssh']['disk_fan']
            cpu_fan = self.configs['pve_ssh']['cpu_fan']
            cpu_temp = self.configs['pve_ssh']['cpu_temp']
            nvme_temp = self.configs['pve_ssh']['nvme_temp']
            sensors_success = False
            cpuinfo_success = False
            if pve_host and pve_port and pve_username and pve_password:
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

                    stdin, stdout, stderr = ssh.exec_command('sensors -j')
                    stdout_result = stdout.read().decode()
                    stderr_result = stderr.read().decode()
                    if stdout_result:
                        sensors = json.loads(stdout_result)
                        # self.configs['pve']['sensors'] = sensors
                        self.data['pve_disk_fan_value'] = self.get_value(sensors, disk_fan)
                        self.data['pve_cpu_fan_value'] = self.get_value(sensors, cpu_fan)
                        self.data['pve_cpu_temp_value'] = self.get_value(sensors, cpu_temp)
                        self.data['pve_nvme_temp_value'] = self.get_value(sensors, nvme_temp)
                        sensors_success = True
                    elif stderr_result:
                        self._write_log(f'_check_pve_ssh sensors {stderr_result}')

                    stdin, stdout, stderr = ssh.exec_command("cat /proc/cpuinfo | grep 'MHz'")
                    stdout_result = stdout.read().decode()
                    stderr_result = stderr.read().decode()
                    if stdout_result:
                        cpufreqs = []
                        for line in stdout_result.split('\n'):
                            if line:
                                cpufreqs.append(float(line.split(':')[1].strip()))
                        self.data['pve_cpu_freq'] = round(sum(cpufreqs) / len(cpufreqs), 3)
                        cpuinfo_success = True
                    elif stderr_result:
                        self._write_log(f'_check_pve_ssh cpuinfo {stderr_result}')
                except Exception as e:
                    ssh = None
                    self._write_log(f'_check_pve_ssh {str(e)}')
                    pass

            if not sensors_success:
                self.data['pve_disk_fan_value'] = 'N/A'
                self.data['pve_cpu_fan_value'] = 'N/A'
                self.data['pve_cpu_temp_value'] = 'N/A'
                self.data['pve_nvme_temp_value'] = 'N/A'
            if not cpuinfo_success:
                self.data['pve_cpu_freq'] = 'N/A'
            time.sleep(1)
        if ssh:
            ssh.close()

    def _check_nas_disk(self):
        api = None
        while not self.is_stop:
            dsm_host = self.get_value(self.configs, 'dsm.host', None)
            dsm_port = self.get_value(self.configs, 'dsm.port', None)
            dsm_username = self.get_value(self.configs, 'dsm.username', None)
            dsm_password = self.get_value(self.configs, 'dsm.password', None)

            dsm_success = False
            if dsm_host and dsm_port and dsm_username and dsm_password:
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
                        for disk in dsm_storage['data']['disks']:
                            utilization = None
                            for disk_utilization in dsm_disk_utilization['disk']:
                                if disk_utilization['device'] == disk['id']:
                                    utilization = disk_utilization
                                    break
                            disk['utilization'] = None if not utilization else utilization

                    self.data['dsm_storage'] = dsm_storage
                    self.data['dsm_disk_utilization'] = dsm_disk_utilization

                except Exception as e:
                    api = None
                    self._write_log(f'_check_nas_disk {str(e)}')

            # if not dsm_success:
            #     self.data['dsm_storage'] = None
            #     self.data['dsm_disk_utilization'] = None

            time.sleep(1)

    def _check_homeassistant(self):
        while not self.is_stop:
            address = self.get_value(self.configs, 'homeassistant.address', None)
            token = self.get_value(self.configs, 'homeassistant.token', None)
            success = False
            if address and token:
                try:
                    url = f'{address}/api/states'
                    headers = {'Authorization': f'Bearer {token}'}
                    r = requests.get(url, headers=headers)
                    r.close()
                    data = r.json()
                    for item in data:
                        for sensor in self.get_value(self.configs, 'homeassistant.sensors', []):
                            if sensor['id'] == item['entity_id']:
                                sensor['value'] = item['state']
                                sensor['unit'] = self.get_value(item, 'attributes.unit_of_measurement', '')
                                sensor['unit'] = '' if not sensor['unit'] else sensor['unit']
                                break

                        if self.get_value(self.configs, 'homeassistant.pve_power_sensor_id') and item[
                            'entity_id'] == self.get_value(self.configs, 'homeassistant.pve_power_sensor_id'):
                            self.data['pve_power'] = float(item['state'])
                            self.data['pve_power_unit'] = self.get_value(item, 'attributes.unit_of_measurement', '')
                            self.data['pve_power_unit'] = '' if not self.data['pve_power_unit'] else self.data[
                                'pve_power_unit']

                    self.data['homeassistant'] = self.configs['homeassistant']['sensors']
                    success = True
                except Exception as e:
                    self._write_log(f'_check_homeassistant {str(e)}')
            if not success:
                self.data['pve_power'] = 'N/A'
                self.data['pve_power_unit'] = 'N/A'
            time.sleep(1)

    def format_timeout(self, address, key):
        if key in address:
            if address[key]:
                return f"[{self.color_green}]{address[key]} ms[/{self.color_green}]"
            else:
                return f"[{self.color_red}]timeout[/{self.color_red}]"
        else:
            return f"[{self.color_yellow}]loading[/{self.color_yellow}]"

    def format_port(self, address, key):
        if key in address:
            if address[key]:
                return f"[{self.color_green}]open[/{self.color_green}]"
            else:
                return f"[{self.color_red}]closed[/{self.color_red}]"
        else:
            return f"[{self.color_yellow}]loading[/{self.color_yellow}]"

    def format_size(self, size, color=False):
        if size == 'N/A' or size is None or size == '':
            return size
        size = float(size)
        result = ""

        if size < 1024:
            color = self.color_green if color else False
            result = f"{size} B"
        elif size < 1024 * 1024:
            color = self.color_yellow if color else False
            result = f"{round(size / 1024, 2)} KB"
        elif size < 1024 * 1024 * 1024:
            color = self.color_purple if color else False
            result = f"{round(size / 1024 / 1024, 2)} MB"
        elif size < 1024 * 1024 * 1024 * 1024:
            color = self.color_blue if color else False
            result = f"{round(size / 1024 / 1024 / 1024, 2)} GB"
        else:
            color = self.color_red if color else False
            result = f"{round(size / 1024 / 1024 / 1024 / 1024, 2)} TB"

        if color:
            result = f"[{color}]{result}[/{color}]"

        return result

    def format_usage(self, usage, color=False):
        if usage == 'N/A' or usage is None or usage == '':
            return usage
        usage = float(usage)
        percentage = round(usage * 100, 2)
        if color:
            if percentage < 60:
                color = self.color_green
            elif percentage < 80:
                color = self.color_yellow
            else:
                color = self.color_red
        result = f"{percentage} %"
        if color:
            result = f"[{color}]{result}[/{color}]"
        return result

    def format_temp(self, temp, color=False):
        if temp == 'N/A' or temp is None or temp == '':
            return temp
        temp = float(temp)
        if color:
            if temp < 50:
                color = self.color_green
            elif temp < 70:
                color = self.color_yellow
            else:
                color = self.color_red
        result = f"{temp} °C"
        if color:
            result = f"[{color}]{result}[/{color}]"
        return result

    def format_hdd_temp(self, temp, color=False):
        if temp == 'N/A' or temp is None or temp == '':
            return temp
        temp = float(temp)
        if color:
            if temp <= 35:
                color = self.color_green
            elif temp <= 45:
                color = self.color_yellow
            else:
                color = self.color_red
        result = f"{temp} °C"
        if color:
            result = f"[{color}]{result}[/{color}]"
        return result

    def format_power(self, value, color=False):
        if value == 'N/A' or value is None or value == '':
            return value
        value = float(value)
        if color:
            if value <= 40:
                color = self.color_green
            elif value <= 60:
                color = self.color_yellow
            else:
                color = self.color_red
        result = f"{value} W"
        if color:
            result = f"[{color}]{result}[/{color}]"
        return result

    def get_value(self, data, key, default=None):
        key = key.split('.')
        for k in key:
            if k in data and data[k] is not None:
                data = data[k]
            else:
                return default
        return data

    def run(self):
        self.threads = []
        for address in self.addresses:
            self.threads.append(threading.Thread(target=self._check_timeout, args=(address,)))

        for address in self.get_value(self.configs, 'addresses', []):
            self.threads.append(
                threading.Thread(target=self._check_port, args=(address['local'], address['local_port'])))
            self.threads.append(
                threading.Thread(target=self._check_port, args=(address['public'], address['public_port'])))

        self.threads.append(threading.Thread(target=self._check_nas_disk))
        self.threads.append(threading.Thread(target=self._check_pve_web))
        self.threads.append(threading.Thread(target=self._check_pve_ssh))
        self.threads.append(threading.Thread(target=self._check_homeassistant))
        if self.web_gui:
            self.threads.append(threading.Thread(target=self._web))
        if self.shell_gui:
            self.threads.append(threading.Thread(target=self._shell))

        for thread in self.threads:
            thread.start()

        while not self.is_stop:
            time.sleep(0.1)

        print(f'\033[1;31m开始关闭程序...\033[0m')

        for thread in self.threads:
            thread.join()

        os.kill(os.getpid(), signal.SIGINT)
        sys.exit(0)


if __name__ == '__main__':
    epilog = '''
Examples:
    # 启动WEB服务
    python main.py -W
    # 通过 shell 输出
    python main.py -S
    # 通过 shell 输出，同时启动WEB服务
    python main.py -S -W
    # 指定自定义配置文件路径和日志保存路径
    python main.py -S -W -C ~/aio_monitor.yaml -L ~/aio_monitor
    '''
    parser = argparse.ArgumentParser(description='AIO Monitor.', epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-W', '--web', metavar='N', type=bool, nargs='?', const=True, default=False,
                        help='启动WEB服务，通过浏览器访问查看信息')
    parser.add_argument('-S', '--shell', metavar='N', type=bool, nargs='?', const=True, default=False,
                        help='通过 shell 输出信息')
    parser.add_argument('-C', '--config', metavar='N', type=str, nargs='?', const=True, default=None,
                        help='配置文件路径，默认为当前程序目录中的 config.yaml')
    parser.add_argument('-L', '--logs', metavar='N', type=str, nargs='?', const=True, default=None,
                        help='日志保存路径，默认为当前程序的 logs 目录')
    parser.add_argument('-V', '--version', action='version', version=f'{__title__} {__version__}')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    Main(web_gui=args.web, shell_gui=args.shell, config_file=args.config, logs_path=args.logs).run()
