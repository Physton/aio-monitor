from rich.layout import Layout


def cli_layout(_configs, _data):
    layouts = []
    if _data['homeassistant_enabled']:
        layouts.append(Layout(name="HomeAssistant", size=4))
    if _data['openwrt_enabled']:
        layouts.append(Layout(name="OpenWrt", size=4))
    if _data['pve_enabled']:
        layouts.append(Layout(name="ProxmoxVE", size=4))
    if _data['server_enabled']:
        layouts.append(Layout(name="ServiceList"))
    if _data['pve_enabled']:
        layouts.append(Layout(name="QemuList"))
    if _data['dsm_enabled']:
        layouts.append(Layout(name="DiskList"))
    layout = Layout(name="root")
    layout.split_column(*layouts)

    return layout
