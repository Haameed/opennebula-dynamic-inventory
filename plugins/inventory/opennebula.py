from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
import os

try:
    from opennebula_api import VirtualMachine, get_all_vms
    from config import load_config
    from utils import sanitize_name, sanitize_attribute
except ImportError as e:
    raise AnsibleError(f"Failed to import required modules: {to_text(e)}")

class InventoryModule(BaseInventoryPlugin):
    NAME = 'snapp.opennebula'

    def verify_file(self, path):
        """Verify that the config file is valid."""
        valid_extensions = ('.yaml', '.yml')
        return os.path.exists(path) and path.endswith(valid_extensions)

    def parse(self, inventory, loader, path, cache=True):
        """Parse the inventory config and populate the inventory."""
        super().parse(inventory, loader, path, cache)
        try:
            # Get config path from plugin config or environment
            config_path = self.get_option('config_path') or os.environ.get('CONFIG_PATH', 'opennebula.yaml')
            if not os.path.exists(config_path):
                raise AnsibleError(f"Configuration file not found at {config_path}. Generate one using generate_config.py.")

            # Load configuration
            config = load_config(config_path)
            vm_rule_set = config.get('vm_rule_set', 'vm_default')
            label_rule_set = config.get('label_rule_set', 'label_default')
            attribute_rule_sets = config.get('attribute_rule_sets', [])
            sanitization_rules = config.get('sanitization_rules', {})
            servers = config.get('servers', [])

            if not servers:
                raise AnsibleError("No servers defined in configuration.")

            # Fetch VMs from OpenNebula
            vms = []
            for server in servers:
                try:
                    vms.extend(get_all_vms(server))
                except Exception as e:
                    self.display.warning(f"Failed to fetch VMs from {server['endpoint']}: {to_text(e)}")

            # Populate inventory
            self._populate_inventory(vms, vm_rule_set, label_rule_set, attribute_rule_sets, sanitization_rules)

        except Exception as e:
            raise AnsibleError(f"Failed to parse inventory: {to_text(e)}")

    def _populate_inventory(self, vms, vm_rule_set, label_rule_set, attribute_rule_sets, sanitization_rules):
        """Populate the Ansible inventory with VMs, groups, and variables."""
        # Add 'all' group
        self.inventory.add_group('all')

        for vm in vms:
            # Add host
            self.inventory.add_host(vm.vm_name)
            self.inventory.set_variable(vm.vm_name, 'ansible_host', vm.ip_address)
            self.inventory.set_variable(vm.vm_name, 'ansible_port', vm.port)
            self.inventory.add_child('all', vm.vm_name)

            # VM name group
            vm_group = sanitize_name(vm.vm_name, sanitization_rules.get(vm_rule_set, {}))
            if vm_group:
                self.inventory.add_group(vm_group)
                self.inventory.add_child(vm_group, vm.vm_name)

            # Label groups
            for label in vm.labels.split(",") if vm.labels else []:
                label_group = sanitize_name(label.strip(), sanitization_rules.get(label_rule_set, {}))
                if label_group:
                    self.inventory.add_group(label_group)
                    self.inventory.add_child(label_group, vm.vm_name)

            # Attribute groups
            for rule_set in attribute_rule_sets:
                if rule_set.get('attribute') in vm.attributes:
                    attr_value = vm.attributes[rule_set['attribute']]
                    attr_group = sanitize_attribute(attr_value, rule_set)
                    if attr_group:
                        self.inventory.add_group(attr_group)
                        self.inventory.add_child(attr_group, vm.vm_name)