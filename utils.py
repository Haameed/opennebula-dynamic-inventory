import ipaddress

valid_ranges = [
    "172.20.0.0/16",
    "172.21.6.0/24",
]

def verify_ip_address(ip_address):
    try:
        ip = ipaddress.ip_address(ip_address)
        for net_range in valid_ranges:
            network = ipaddress.ip_network(net_range, strict=False)
            if ip in network:
                return True
        return False
    except ValueError:
        return False