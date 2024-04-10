import os
import time


class Log:
    logs_path = None

    def __init__(self, logs_path):
        self.logs_path = logs_path

    def clear(self, max_num=3):
        files = os.listdir(self.logs_path)
        files = [file for file in files if file.endswith('.log')]
        files.sort()
        if len(files) > max_num:
            for file in files[:-max_num]:
                os.remove(os.path.join(self.logs_path, file))

    def get_file(self):
        file = os.path.join(self.logs_path, f'{time.strftime("%Y%m%d%H")}.log')
        if not os.path.exists(file):
            open(file, 'w').close()
            self.clear()
        return file

    def write(self, log):
        log = f'{time.strftime("%Y-%m-%d %H:%M:%S")} {log}\n'
        file = self.get_file()
        with open(file, 'a') as f:
            f.write(log)
