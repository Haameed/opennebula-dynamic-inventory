import re
from typing import List, Dict, Any
import logging


class VirtualMachine:
    def __init__(self, vm_name: str, vm_ip: str, vm_port: int, labels: str):
        self.vm_name = vm_name
        self.vm_ip = vm_ip
        self.vm_port = vm_port
        self.labels = labels

def create_inventory(vms: List[VirtualMachine]) -> Dict[str, Any]:
    host_vars = {}
    groups = {}

    for vm in vms:
        vm_name = vm.vm_name.strip()
        vmport = vm.vm_port
        vm_ip = vm.vm_ip.strip()
        labels = vm.labels
        if not vm_name or not vm_ip:
            logging.error("faild to fetch vminfo")

        host_vars[vm_name] = {
            "ansible_host": vm_ip,
            "ansible_port": vmport,
        }

        group_name = sanitize_group_name(vm_name)
        if not group_name:
            continue

        if group_name not in groups:
            groups[group_name] = {
                "hosts": [],
                "vars": {},
                "children": [],
            }
        if vm_name not in groups[group_name]["hosts"]:
            groups[group_name]["hosts"].append(vm_name)
        for label in labels.split(","): 
            label_name = sanitize_label_name(label)
            if not label_name:
                continue
            if label_name not in groups:
                groups[label_name] = {
                "hosts": [],
                "vars": {},
                "children": [],
            }
            if vm_name not in groups[label_name]["hosts"]:
                groups[label_name]["hosts"].append(vm_name) 

    data = {}
    sorted_groups = sort_groups(groups)
    for group_name in sorted_groups:
        data[group_name] = groups[group_name]

    data["_meta"] = {"hostvars": host_vars}
    data["all"] = {
        "hosts": get_all_hosts(groups),
        "children": sorted_groups,
    }

    return data

number_suffix = re.compile(r'[-]?[0-9].*')

def sanitize_group_name(name: str) -> str:
    name = name.split(".", 1)[0]
    name = number_suffix.sub("", name)
    name = name.replace("-", "_")
    return name.strip().lower()

def sanitize_label_name(name: str) -> str:
    name = name.replace("-", "_")
    name = name.replace(".", "_")
    return name.strip().lower()

def sort_groups(groups: Dict[str, Any]) -> List[str]:
    return list(set(sorted(groups.keys())))

def get_all_hosts(groups: Dict[str, Any]) -> List[str]:
    all_hosts = []
    for group_data in groups.values():
        all_hosts.extend(group_data["hosts"])
    return sorted(list(set(all_hosts)))
