import os
import sys
import yaml
import re
from typing import List, Tuple, Dict, Any

class Config:
    def __init__(self, url: str, port: int, user: str, password: str):
        self.url = url
        self.user = user
        self.password = password
        self.port = port
        self.endpoint = f"{self.url}:{self.port}/RPC2"

def load_config(config_path: str = None) -> Tuple[List[Config], str, str, List[Dict[str, Any]], Dict[str, Any]]:
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config.yaml")

    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}. Run './main.py --generate-config' to create a sample config.")
        sys.exit(1)

    try:
        with open(config_path, "r") as file:
            config_data = yaml.safe_load(file)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {config_path}: {e}")
        sys.exit(1)

    if not isinstance(config_data, dict) or "servers" not in config_data:
        print("Config file must contain a 'servers' key with a list of server configurations")
        sys.exit(1)

    # Load sanitization rules
    sanitization_rules = config_data.get("sanitization_rules", {})
    if not isinstance(sanitization_rules, dict):
        print("sanitization_rules must be a dictionary")
        sys.exit(1)

    # Validate sanitization rules
    for rule_set_name, rule_set in sanitization_rules.items():
        if not isinstance(rule_set, dict) or "prefix" not in rule_set or "name_rules" not in rule_set:
            print(f"Invalid rule set {rule_set_name}: must contain 'prefix' and 'name_rules'")
            sys.exit(1)
        if not isinstance(rule_set["prefix"], str):
            print(f"Prefix in rule set {rule_set_name} must be a string")
            sys.exit(1)
        if not isinstance(rule_set["name_rules"], list):
            print(f"name_rules in rule set {rule_set_name} must be a list")
            sys.exit(1)
        for rule in rule_set["name_rules"]:
            if not isinstance(rule, dict) or "pattern" not in rule or "replacement" not in rule:
                print(f"Invalid rule in {rule_set_name}: {rule}")
                sys.exit(1)
            try:
                re.compile(rule["pattern"])
            except re.error as e:
                print(f"Invalid regex pattern in {rule_set_name}: {rule['pattern']}: {e}")
                sys.exit(1)

    # Load rule set names
    vm_rule_set = config_data.get("vm_rule_set", "vm_default")
    label_rule_set = config_data.get("label_rule_set", "label_default")
    if vm_rule_set not in sanitization_rules:
        print(f"vm_rule_set '{vm_rule_set}' not found in sanitization_rules")
        sys.exit(1)
    if label_rule_set not in sanitization_rules:
        print(f"label_rule_set '{label_rule_set}' not found in sanitization_rules")
        sys.exit(1)

    attribute_rule_sets = config_data.get("attribute_rule_sets", [])
    if not isinstance(attribute_rule_sets, list):
        print("attribute_rule_sets must be a list")
        sys.exit(1)
    for rule_set in attribute_rule_sets:
        if not isinstance(rule_set, dict) or not all(k in rule_set for k in ["name", "attribute", "prefix", "value_rules"]):
            print(f"Invalid attribute rule set: {rule_set}")
            sys.exit(1)
        if not isinstance(rule_set["name"], str) or not isinstance(rule_set["attribute"], str) or not isinstance(rule_set["prefix"], str):
            print(f"Invalid types in attribute rule set {rule_set['name']}: name, attribute, and prefix must be strings")
            sys.exit(1)
        if not isinstance(rule_set["value_rules"], list):
            print(f"value_rules in attribute rule set {rule_set['name']} must be a list")
            sys.exit(1)
        for rule in rule_set["value_rules"]:
            if not isinstance(rule, dict) or "pattern" not in rule or "replacement" not in rule:
                print(f"Invalid rule in attribute rule set {rule_set['name']}: {rule}")
                sys.exit(1)
            try:
                re.compile(rule["pattern"])
            except re.error as e:
                print(f"Invalid regex pattern in attribute rule set {rule_set['name']}: {rule['pattern']}: {e}")
                sys.exit(1)

    servers = config_data["servers"]
    if not isinstance(servers, list):
        print("'servers' must be a list of server configurations")
        sys.exit(1)

    configs = []
    for idx, server in enumerate(servers, 1):
        url = server.get("endpoint")
        port = server.get("port")
        user = server.get("user")
        password = server.get("password")
        if not all([url, user, password, port]):
            print(f"Server configuration {idx} missing required fields: endpoint, user, password, or port")
            sys.exit(1)
        configs.append(Config(url, port, user, password))

    if not configs:
        print("Config file must contain at least one valid server configuration")
        sys.exit(1)

    return configs, vm_rule_set, label_rule_set, attribute_rule_sets, sanitization_rules