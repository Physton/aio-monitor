import os
import sys
import time
import threading
import signal
import yaml
import argparse
import hashlib
import traceback
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
import warnings
import urllib3.exceptions
from utils.get_all_ipv4 import get_all_ipv4
from utils.get_value import get_value
from utils.log import Log
from utils.print_error import print_error
from utils.check_pve_web import check_pve_web
from utils.check_pve_ssh import check_pve_ssh, close_pve_ssh
from utils.check_nas_disk import check_nas_disk
from utils.check_homeassistant import check_homeassistant
from utils.check_op_ssh import check_op_ssh, close_op_ssh
from utils.check_timeout import check_timeout
from utils.check_port import check_port
from utils.cli_richs import cli_richs
from utils.cli_layout import cli_layout
from utils.cli_homeassistant import cli_homeassistant
from utils.cli_openwrt import cli_openwrt
from utils.cli_pve import cli_pve
from utils.cli_server import cli_server
from utils.cli_pve_qemus import cli_pve_qemus
from utils.cli_dsm_disks import cli_dsm_disks

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
    data = {
        'homeassistant_enabled': False,
        'openwrt_enabled': False,
        'pve_enabled': False,
        'server_enabled': False,
        'dsm_enabled': False,
    }
    app = None
    server = None
    log = None

    console = Console()

    def __init__(self, web_gui=True, shell_gui=True, config_file=None, logs_path=None):
        self.web_gui = web_gui
        self.shell_gui = shell_gui

        if not config_file:
            self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
        else:
            self.config_file = config_file
        if not os.path.isfile(self.config_file):
            print_error(f'config file not found: {self.config_file}')
            sys.exit(1)

        if not logs_path:
            self.logs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        else:
            self.logs_path = logs_path

        if not os.path.isdir(self.logs_path):
            print_error(f'logs path not found: {self.logs_path}')
            sys.exit(1)
        self.log = Log(self.logs_path)

        try:
            self.configs = yaml.load(open(self.config_file), Loader=yaml.FullLoader)
            self.data['app_background_image'] = get_value(self.configs, 'app_background_image', '')
            self.data['app_background_blur'] = get_value(self.configs, 'app_background_blur', 0)
            self.data['app_card_background_color'] = get_value(self.configs, 'app_card_background_color',
                                                               'rgba(64, 75, 105, 1)')
        except Exception as e:
            print_error(f'config file error: {str(e)}')
            traceback.print_exc()
            sys.exit(1)

        self._parse_addresses()
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, signal, frame):
        self.is_stop = True
        if self.server:
            self.server.handle_exit(signal, frame)

    def _parse_addresses(self):
        self.addresses = []
        for address in get_value(self.configs, 'addresses', []):
            self.data['server_enabled'] = True
            if address['local'] not in self.addresses:
                self.addresses.append(address['local'])
            if address['public'] not in self.addresses:
                self.addresses.append(address['public'])

    def _web(self):
        app_host = get_value(self.configs, 'app_host', '0.0.0.0')
        app_port = get_value(self.configs, 'app_port', '8000')
        app_secret = get_value(self.configs, 'app_secret', None)
        app_expire = get_value(self.configs, 'app_expire', None)
        app_username = get_value(self.configs, 'app_username', None)
        app_password = get_value(self.configs, 'app_password', None)
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
                        self.data['addresses'] = get_value(self.configs, 'addresses', [])
                        return {"data": self.data}
                else:
                    @self.app.get("/api/data")
                    def api_data():
                        self.data['addresses'] = get_value(self.configs, 'addresses', [])
                        return {"data": self.data}

                self.app.mount("/", StaticFiles(directory="./html", html=True), name="static")

                ipv4s = get_all_ipv4()
                for ipv4 in ipv4s:
                    print(f'Web: http://{ipv4}:{app_port}')
                print("")

                log_level = 'error' if self.shell_gui else 'info'
                config = uvicornConfig(self.app, host=app_host, port=int(app_port), log_level=log_level)
                self.server = Server(config)
                self.server.run()
            except Exception as e:
                self.log.write(f'_web {str(e)}')
                self.log.write(traceback.format_exc())

    def _shell(self):
        richs = cli_richs(self.configs, self.data)
        layout = cli_layout(self.configs, self.data)
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while not self.is_stop:
                # live.console.clear()

                cli_homeassistant(self.configs, self.data, richs, layout)
                cli_openwrt(self.configs, self.data, richs, layout)
                cli_pve(self.configs, self.data, richs, layout)
                cli_server(self.configs, self.data, richs, layout)
                cli_pve_qemus(self.configs, self.data, richs, layout)
                cli_dsm_disks(self.configs, self.data, richs, layout)

                # live.console.print(ha_columns)
                # live.console.print(pve_columns)
                # live.console.print(server_table)
                # live.console.print(pve_qemus_table)
                # live.console.print(disks_table)
                # live.update([pve_columns, server_table, pve_qemus_table, disks_table])
                time.sleep(1)

    def _check_timeout(self, address):
        while not self.is_stop:
            check_timeout(self.configs, self.data, self.log, address)
            time.sleep(1)

    def _check_port(self, address, port):
        while not self.is_stop:
            check_port(self.configs, self.data, self.log, address, port)
            time.sleep(3)

    def _check_pve_web(self):
        while not self.is_stop:
            check_pve_web(self.configs, self.data, self.log)
            time.sleep(1)

    def _check_pve_ssh(self):
        while not self.is_stop:
            check_pve_ssh(self.configs, self.data, self.log)
            time.sleep(1)
        close_pve_ssh()

    def _check_nas_disk(self):
        while not self.is_stop:
            check_nas_disk(self.configs, self.data, self.log)
            time.sleep(1)

    def _check_homeassistant(self):
        while not self.is_stop:
            check_homeassistant(self.configs, self.data, self.log)
            time.sleep(1)

    def _check_op_ssh(self):
        while not self.is_stop:
            check_op_ssh(self.configs, self.data, self.log)
            time.sleep(1)
        close_op_ssh()

    def run(self):
        self.threads = []
        for address in self.addresses:
            self.threads.append(threading.Thread(target=self._check_timeout, args=(address,)))

        for address in get_value(self.configs, 'addresses', []):
            self.threads.append(
                threading.Thread(target=self._check_port, args=(address['local'], address['local_port'])))
            self.threads.append(
                threading.Thread(target=self._check_port, args=(address['public'], address['public_port'])))

        self.threads.append(threading.Thread(target=self._check_nas_disk))
        self.threads.append(threading.Thread(target=self._check_pve_web))
        self.threads.append(threading.Thread(target=self._check_pve_ssh))
        self.threads.append(threading.Thread(target=self._check_homeassistant))
        self.threads.append(threading.Thread(target=self._check_op_ssh))
        if self.web_gui:
            self.threads.append(threading.Thread(target=self._web))
        if self.shell_gui:
            self.threads.append(threading.Thread(target=self._shell))

        for thread in self.threads:
            thread.start()

        while not self.is_stop:
            time.sleep(0.1)

        print_error('开始关闭程序...')

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

    main = Main(web_gui=args.web, shell_gui=args.shell, config_file=args.config, logs_path=args.logs)
    main.run()
