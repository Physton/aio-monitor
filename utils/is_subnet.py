import ipaddress


def is_subnet(ip, subnets):
    for subnet in subnets:
        temp_ip = ipaddress.ip_address(ip)
        temp_subnet = ipaddress.ip_network(subnet)
        if temp_ip in temp_subnet:
            return True
    return False
