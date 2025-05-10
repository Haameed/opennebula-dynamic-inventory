# OpenNebula Inventory Plugin Documentation

This plugin generates a dynamic Ansible inventory from OpenNebula VMs, grouping by VM names, labels, and attributes.

## Configuration

The plugin uses a YAML configuration file (`dynamic_inventory/config.yaml`). Generate a sample:
```bash
~/.ansible/collections/ansible_collections/sysops/opennebula_inventory/plugins/inventory/opennebula.py --generate-config
```

### Example Config
See the `README.md` for a comprehensive example. A minimal config includes:
```yaml
vm_rule_set: vm_default
label_rule_set: label_default
attribute_rule_sets:
  - name: port_group
    attribute: SSH_PORT
    prefix: port_
    value_rules: []
sanitization_rules:
  vm_default:
    prefix: vm_
    name_rules:
      - pattern: ^([a-zA-Z]+)\..*
        replacement: $1
servers:
  - endpoint: http://your-opennebula-server
    port: 2633
    user: your_username
    password: your_password
```

### Configuration Options
- **`vm_rule_set`**: Rule set for VM names (e.g., `vm_default`).
- **`label_rule_set`**: Rule set for labels (e.g., `label_default`).
- **`attribute_rule_sets`**: List of rules for attribute-based grouping.
  - `name`: Unique rule set name.
  - `attribute`: Attribute key (e.g., `SSH_PORT`).
  - `prefix`: Group prefix (e.g., `port_`).
  - `value_rules`: Regex rules for attribute values.
- **`sanitization_rules`**: Named rule sets for VM names and labels.
  - `prefix`: Group prefix.
  - `name_rules`: List of regex patterns and replacements.
- **`servers`**: List of OpenNebula servers.
  - `endpoint`: Server URL.
  - `port`: RPC port.
  - `user`: Username.
  - `password`: Password.

## Usage
Test the inventory:
```bash
ansible-inventory -i sysops.opennebula --list
```

Run Ansible:
```bash
ansible -i sysops.opennebula all -m ping
```

## Requirements
- pyone
- pyyaml

Install:
```bash
pip install -r ~/.ansible/collections/ansible_collections/sysops/opennebula_inventory/requirements.txt
```

## License
GPL-3.0-or-later