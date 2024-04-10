import netifaces


def get_all_ipv4():
    ips = []
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            ips.extend([addr['addr'] for addr in addrs[netifaces.AF_INET]])
    return ips
