
import os
import sys
import yaml
import re
import argparse
from dataclasses import dataclass
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text

try:
    import pyone
except ImportError:
    raise AnsibleError("The 'pyone' module is required for this inventory plugin")

DOCUMENTATION = r'''
  name: opennebula
  plugin_type: inventory
  short_description: Dynamic inventory plugin for OpenNebula
  description:
    - Fetches virtual machines (VMs) from OpenNebula servers and groups them by names, labels, and attributes (e.g., SSH_PORT, ROLE).
    - Supports regex-based sanitization for group names.
    - Generates a sample configuration file with ~/.ansible/collections/ansible_collections/snapp/opennebula/plugins/inventory/opennebula.py --generate-config.
  options:
    config_path:
      description: Path to the YAML configuration file (opennebula.yaml).
      type: path
      required: true
  extends_documentation_fragment:
    - inventory_cache
'''

@dataclass
class VirtualMachine:
    vm_name: str
    ip_address: str
    port: int
    labels: str
    attributes: dict

class InventoryModule(BaseInventoryPlugin):
    NAME = 'snapp.opennebula'

    def __init__(self):
        super().__init__()
        self._config_data = None

    def verify_file(self, path):
        """Verify that the config file is valid."""
        valid_extensions = ('.yaml', '.yml')
        return os.path.exists(path) and path.endswith(valid_extensions)

    def parse(self, inventory, loader, path, cache=True):
        """Parse the inventory config and populate the inventory."""
        super().parse(inventory, loader, path, cache)
        self._config_data = self._read_config_data(path)
        try:
            # Handle --generate-config flag
            if '--generate-config' in sys.argv:
                self.generate_config()
                sys.exit(0)
            config_path = self.get_option('config_path') or os.environ.get('CONFIG_PATH', '')
            if not os.path.exists(config_path):
                raise AnsibleError(f"Configuration file not found at {config_path}. Run ~/.ansible/collections/ansible_collections/snapp/opennebula/plugins/inventory/opennebula.py --generate-config to create one.")
            config = self.load_config(config_path)
            vm_rule_set = config.get('vm_rule_set', 'vm_default')
            label_rule_set = config.get('label_rule_set', 'label_default')
            attribute_rule_sets = config.get('attribute_rule_sets', [])
            sanitization_rules = config.get('sanitization_rules', {})
            servers = config.get('servers', [])

            if not servers:
                raise AnsibleError("No servers defined in configuration.")
            vms = self.get_all_vms(servers)
            self._populate_inventory(vms, vm_rule_set, label_rule_set, attribute_rule_sets, sanitization_rules)

        except Exception as e:
            raise AnsibleError(f"Failed to parse inventory: {to_text(e)}")

    def load_config(self, config_path):
        """Load and validate the YAML configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            raise AnsibleError(f"Failed to load configuration {config_path}: {to_text(e)}")
        return config

    def get_all_vms(self, servers):
        """Fetch all VMs from OpenNebula servers using infoextended."""
        vms = []
        for server in servers:
            try:
                endpoint = f"{server['endpoint']}:{server.get('port', 2633)}/RPC2"
                session = f"{server['user']}:{server['password']}"
                client = pyone.OneServer(endpoint, session)
                vm_pool = client.vmpool.infoextended(-2, -1, -1, -1)                    
                if not hasattr(vm_pool, 'VM') or not vm_pool.VM:
                    self.display.warning(f"No VMs found for {server['endpoint']}")
                    continue
                for vm in vm_pool.VM:
                    vm_state = vm.STATE
                    if vm_state == 3:  # Only process running VMs
                        ip_address = None
                        nics = vm.TEMPLATE.get('NIC', [])
                        if isinstance(nics, list):
                            if not nics:
                                continue
                            first_nic = nics[0]
                            ip_address = first_nic.get("IP")
                        else:
                            ip_address = nics.get("IP")
                        if not ip_address:
                            self.display.warning(f"Skipping VM {vm.NAME}: No IP address found")
                            continue
                        ssh_port = vm.USER_TEMPLATE.get("SSH_PORT", 22)
                        attributes = {}
                        for k, v in vm.USER_TEMPLATE.items():
                            if isinstance(v, str) and k not in ('NIC', 'DISK', 'CONTEXT'):
                                attributes[k] = v

                        labels = vm.USER_TEMPLATE.get('LABELS', '')
                        if not labels:
                            self.display.warning(f"No labels found for VM {vm.NAME}")
                        vms.append(VirtualMachine(
                            vm_name=vm.NAME.lower().strip(),
                            ip_address=ip_address,
                            port=ssh_port,
                            labels=labels,
                            attributes=attributes
                        ))
            except Exception as e:
                self.display.warning(f"Failed to fetch VMs from {server['endpoint']}: {to_text(e)}")
        return vms

    def sanitize_name(self, name, rule_set):
        """Sanitize a name (VM or label) using the provided rule set."""
        if not name or not rule_set:
            return None
        prefix = rule_set.get('prefix', '')
        result = name
        for rule in rule_set.get('name_rules', []):
            pattern = rule.get('pattern', '')
            replacement = rule.get('replacement', '')
            try:
                result = re.sub(pattern, replacement, result)
                result = result
            except Exception as e:
                self.display.warning(f"Failed to apply rule {pattern} to {name}: {to_text(e)}")
        sanitized = f"{prefix}{result}".lower().rstrip() if result.strip() else None
        return sanitized

    def sanitize_attribute(self, value, rule_set):
        """Sanitize an attribute value using the provided rule set."""
        if not value or not rule_set:
            return None
        prefix = rule_set.get('prefix', '')
        result = str(value)
        for rule in rule_set.get('value_rules', []):
            pattern = rule.get('pattern', '')
            replacement = rule.get('replacement', '')
            try:
                result = re.sub(pattern, replacement, result)
            except Exception as e:
                self.display.warning(f"Failed to apply rule {pattern} to {value}: {to_text(e)}")
        sanitized = f"{prefix}{result}".lower().rstrip() if result.strip() else None
        return sanitized

    def _populate_inventory(self, vms, vm_rule_set, label_rule_set, attribute_rule_sets, sanitization_rules):
        """Populate the Ansible inventory with VMs, groups, and variables."""
        self.inventory.add_group('all')

        for vm in vms:
            self.inventory.add_host(vm.vm_name)
            self.inventory.set_variable(vm.vm_name, 'ansible_host', vm.ip_address)
            self.inventory.set_variable(vm.vm_name, 'ansible_port', vm.port)
            self.inventory.add_child('all', vm.vm_name)

            # VM name group
            vm_group = self.sanitize_name(vm.vm_name, sanitization_rules.get(vm_rule_set, {}))
            if vm_group:
                self.inventory.add_group(vm_group)
                self.inventory.add_child(vm_group, vm.vm_name)
            else:
                self.display.vvv(f"No valid VM group for {vm.vm_name}")

            # Label groups
            labels = vm.labels.split(",") if vm.labels else []
            for label in labels:
                label = label.strip()
                if label:
                    label_group = self.sanitize_name(label, sanitization_rules.get(label_rule_set, {}))
                    if label_group:
                        self.inventory.add_group(label_group)
                        self.inventory.add_child(label_group, vm.vm_name)
                    else:
                        self.display.vvv(f"No valid label group for label '{label}' in VM {vm.vm_name}")

            # Attribute groups
            for rule_set in attribute_rule_sets:
                attr_key = rule_set.get('attribute')
                if attr_key in vm.attributes:
                    attr_value = vm.attributes[attr_key]
                    attr_group = self.sanitize_attribute(attr_value, rule_set)
                    if attr_group:
                        self.inventory.add_group(attr_group)
                        self.inventory.add_child(attr_group, vm.vm_name)
                    else:
                        self.display.vvv(f"No valid attribute group for {attr_key}={attr_value} in VM {vm.vm_name}")
                else:
                    self.display.vvv(f"Attribute {attr_key} not found in VM {vm.vm_name}")

    def generate_config(self, output_dir='.'):
        """Generate a sample opennebula.yaml configuration file."""
        config = {
            'vm_rule_set': 'vm_default',
            'label_rule_set': 'label_default',
            'attribute_rule_sets': [
                {
                    'attribute': 'SSH_PORT',
                    'name': 'port_group',
                    'prefix': 'port_',
                    'value_rules': []
                }
            ],
            'sanitization_rules': {
                'vm_default': {
                    'prefix': 'vm_',
                    'name_rules': [
                        {'pattern': '^([^.]+).*', 'replacement': '\\1'},
                        {'pattern': '-\\d+$', 'replacement': ''},
                        {'pattern': '-', 'replacement': '_'}
                    ]
                },
                'label_default': {
                    'prefix': 'label_',
                    'name_rules': [
                        {'pattern': '[\\-\\.]', 'replacement': '_'}
                    ]
                }
            },
            'servers': [
                {
                    'endpoint': 'http://your-first-opennebula-server',
                    'password': 'yourpassword',
                    'port': 2633,
                    'user': 'yourusername'
                },
                {
                    'endpoint': 'http://your-second-opennebula-server',
                    'password': 'yourpassword',
                    'port': 2633,
                    'user': 'yourusername'
                }
            ]
        }

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'opennebula.yaml')
        with open(output_path, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"Sample configuration generated at {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OpenNebula Inventory Plugin')
    parser.add_argument('--generate-config', action='store_true', help='Generate a sample opennebula.yaml')
    args = parser.parse_args()
    if args.generate_config:
        InventoryModule().generate_config()