import ipaddress
import yaml
import os
import sys


# valid_ranges = [
#     "172.20.0.0/16",
#     "172.21.6.0/24",
# ]

# def verify_ip_address(ip_address):
#     try:
#         ip = ipaddress.ip_address(ip_address)
#         for net_range in valid_ranges:
#             network = ipaddress.ip_network(net_range, strict=False)
#             if ip in network:
#                 return True
#         return False
#     except ValueError:
#         return False
    
def generate_sample_config(output_path: str = "config.yaml"):
    sample_config = {
        "vm_rule_set": "vm_default",
        "label_rule_set": "label_default",
        "attribute_rule_sets": [
            {
                "name": "port_group",
                "attribute": "SSH_PORT",
                "prefix": "port_",
                "value_rules": []
            }
        ],
        "sanitization_rules": {
            "vm_default": {
                "prefix": "vm_",
                "name_rules": [
                    {"pattern": r"^([a-zA-Z]+)\..*", "replacement": "$1"},
                    {"pattern": r"[-0-9].*", "replacement": ""},
                    {"pattern": r"-", "replacement": "_"}
                ]
            },
            "label_default": {
                "prefix": "label_",
                "name_rules": [
                    {"pattern": r"[\-\.]", "replacement": "_"}
                ]
            },
            
        },
        "servers": [
            {
                "endpoint": "http://your-opennebula-server",
                "port": 2633,
                "user": "your_username",
                "password": "your_password"
            }
        ]
    }
    
    try:
        # os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as file:
            yaml.dump(sample_config, file, default_flow_style=False, sort_keys=False)
        print(f"Sample config generated at {output_path}")
    except Exception as e:
        print(f"Error generating sample config: {e}")
        sys.exit(1)