class Format:
    color_yellow = "bright_yellow"
    color_red = "bright_red"
    color_blue = "bright_blue"
    color_purple = "purple"
    color_green = "bright_green"

    @staticmethod
    def color(text, color):
        return f"[{color}]{text}[/{color}]"

    @staticmethod
    def bold(text):
        return f"[b]{text}[/b]"

    @staticmethod
    def yellow(text):
        return Format.color(text, Format.color_yellow)

    @staticmethod
    def red(text):
        return Format.color(text, Format.color_red)

    @staticmethod
    def blue(text):
        return Format.color(text, Format.color_blue)

    @staticmethod
    def purple(text):
        return Format.color(text, Format.color_purple)

    @staticmethod
    def green(text):
        return Format.color(text, Format.color_green)

    @staticmethod
    def timeout(address, key):
        if key in address:
            if address[key]:
                return Format.green(f"{address[key]} ms")
            else:
                return Format.red("timeout")
        else:
            return Format.yellow("loading")

    @staticmethod
    def port(address, key):
        if key in address:
            if address[key]:
                return Format.green("open")
            else:
                return Format.red("closed")
        else:
            return Format.yellow("loading")

    @staticmethod
    def size(size, color=False):
        if size == 'N/A' or size is None or size == '':
            return size
        size = float(size)
        result = ""

        if size < 1024:
            color = Format.color_green if color else False
            result = f"{size} B"
        elif size < 1024 * 1024:
            color = Format.color_yellow if color else False
            result = f"{round(size / 1024, 2)} KB"
        elif size < 1024 * 1024 * 1024:
            color = Format.color_purple if color else False
            result = f"{round(size / 1024 / 1024, 2)} MB"
        elif size < 1024 * 1024 * 1024 * 1024:
            color = Format.color_blue if color else False
            result = f"{round(size / 1024 / 1024 / 1024, 2)} GB"
        else:
            color = Format.color_red if color else False
            result = f"{round(size / 1024 / 1024 / 1024 / 1024, 2)} TB"

        if color:
            result = Format.color(result, color)

        return result

    @staticmethod
    def size_flow(size, color=False):
        if size == 'N/A' or size is None or size == '':
            return size
        size = float(size)
        result = ""

        if size < 1024:
            color = Format.color_green if color else False
            result = f"{size} B/s"
        elif size < 1024 * 1024:
            color = Format.color_yellow if color else False
            result = f"{round(size / 1024, 2)} KB/s"
        elif size < 1024 * 1024 * 1024:
            color = Format.color_purple if color else False
            result = f"{round(size / 1024 / 1024, 2)} MB/s"
        elif size < 1024 * 1024 * 1024 * 1024:
            color = Format.color_blue if color else False
            result = f"{round(size / 1024 / 1024 / 1024, 2)} GB/s"
        else:
            color = Format.color_red if color else False
            result = f"{round(size / 1024 / 1024 / 1024 / 1024, 2)} TB/s"

        if color:
            result = Format.color(result, color)

        return result

    @staticmethod
    def usage(usage, color=False):
        if usage == 'N/A' or usage is None or usage == '':
            return usage
        usage = float(usage)
        percentage = round(usage * 100, 2)
        if color:
            if percentage < 60:
                color = Format.color_green
            elif percentage < 80:
                color = Format.color_yellow
            else:
                color = Format.color_red
        result = f"{percentage} %"
        if color:
            result = Format.color(result, color)
        return result

    @staticmethod
    def temp(temp, color=False):
        if temp == 'N/A' or temp is None or temp == '':
            return temp
        temp = float(temp)
        if color:
            if temp < 50:
                color = Format.color_green
            elif temp < 70:
                color = Format.color_yellow
            else:
                color = Format.color_red
        result = f"{temp} °C"
        if color:
            result = Format.color(result, color)
        return result

    @staticmethod
    def hdd_temp(temp, color=False):
        if temp == 'N/A' or temp is None or temp == '':
            return temp
        temp = float(temp)
        if color:
            if temp <= 35:
                color = Format.color_green
            elif temp <= 45:
                color = Format.color_yellow
            else:
                color = Format.color_red
        result = f"{temp} °C"
        if color:
            result = Format.color(result, color)
        return result

    @staticmethod
    def power(value, color=False):
        if value == 'N/A' or value is None or value == '':
            return value
        value = float(value)
        if color:
            if value <= 40:
                color = Format.color_green
            elif value <= 60:
                color = Format.color_yellow
            else:
                color = Format.color_red
        result = f"{value} W"
        if color:
            result = Format.color(result, color)
        return result

    @staticmethod
    def uptime(uptime):
        days = uptime // 86400
        hours = (uptime - days * 86400) // 3600
        minutes = (uptime - days * 86400 - hours * 3600) // 60
        seconds = uptime - days * 86400 - hours * 3600 - minutes * 60
        return f'{days}天{hours}小时{minutes}分钟{seconds}秒'
