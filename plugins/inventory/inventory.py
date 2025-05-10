import re
from typing import List, Dict, Any
import logging

class VirtualMachine:
    def __init__(self, vm_name: str, vm_ip: str, vm_port: int, labels: str, attributes: Dict[str, str]):
        self.vm_name = vm_name
        self.vm_ip = vm_ip
        self.vm_port = vm_port
        self.labels = labels
        self.attributes = attributes

def sanitize_name(name: str, rules: List[Dict[str, str]]) -> str:
    if not name:
        return ""
    result = name
    for rule in rules:
        try:
            result = re.sub(rule["pattern"], rule["replacement"], result)
        except re.error as e:
            logging.warning(f"Skipping invalid regex rule {rule['pattern']}: {e}")
    return result.strip().lower()

def create_inventory(
    vms: List[VirtualMachine],
    vm_rule_set: str,
    label_rule_set: str,
    attribute_rule_sets: List[Dict[str, Any]],
    sanitization_rules: Dict[str, Any]
) -> Dict[str, Any]:
    vm_rules = sanitization_rules.get(vm_rule_set, {"prefix": "", "name_rules": []})
    label_rules = sanitization_rules.get(label_rule_set, {"prefix": "", "name_rules": []})
    vm_prefix = vm_rules.get("prefix", "")
    label_prefix = label_rules.get("prefix", "")
    vm_name_rules = vm_rules.get("name_rules", [])
    label_name_rules = label_rules.get("name_rules", [])
    
    host_vars = {}
    groups = {}

    for vm in vms:
        vm_name = vm.vm_name.strip()
        vmport = vm.vm_port
        vm_ip = vm.vm_ip.strip()
        labels = vm.labels or ""
        attributes = vm.attributes or {}
        if not vm_name or not vm_ip:
            logging.error(f"Failed to fetch VM info for name: {vm_name}, IP: {vm_ip}")
            continue

        host_vars[vm_name] = {
            "ansible_host": vm_ip,
            "ansible_port": vmport,
        }

        group_name = sanitize_name(vm_name, vm_name_rules)
        if group_name:
            group_name = f"{vm_prefix}{group_name}"
            if group_name not in groups:
                groups[group_name] = {
                    "hosts": [],
                    "vars": {},
                    "children": [],
                }
            if vm_name not in groups[group_name]["hosts"]:
                groups[group_name]["hosts"].append(vm_name)

        for label in labels.split(","):
            label_name = sanitize_name(label, label_name_rules)
            if label_name:
                label_name = f"{label_prefix}{label_name}"
                if label_name not in groups:
                    groups[label_name] = {
                        "hosts": [],
                        "vars": {},
                        "children": [],
                    }
                if vm_name not in groups[label_name]["hosts"]:
                    groups[label_name]["hosts"].append(vm_name)

        for rule_set in attribute_rule_sets:
            attribute = rule_set["attribute"]
            prefix = rule_set["prefix"]
            value_rules = rule_set["value_rules"]
            if attribute in attributes:
                value = attributes[attribute]
                group_name = sanitize_name(value, value_rules)
                if group_name:
                    group_name = f"{prefix}{group_name}"
                    if group_name not in groups:
                        groups[group_name] = {
                            "hosts": [],
                            "vars": {},
                            "children": [],
                        }
                    if vm_name not in groups[group_name]["hosts"]:
                        groups[group_name]["hosts"].append(vm_name)

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

def sort_groups(groups: Dict[str, Any]) -> List[str]:
    return list(set(sorted(groups.keys())))

def get_all_hosts(groups: Dict[str, Any]) -> List[str]:
    all_hosts = []
    for group_data in groups.values():
        all_hosts.extend(group_data["hosts"])
    return sorted(list(set(all_hosts)))