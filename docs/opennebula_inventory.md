# OpenNebula Inventory Plugin Documentation
This plugin generates a dynamic Ansible inventory from OpenNebula VMs, grouping by VM names, labels, and attributes.

## Configuration
The plugin uses a YAML configuration file (dynamic_inventory/config.yaml). Generate a sample:

bash
~/.ansible/collections/ansible_collections/sysops/opennebula_inventory/plugins/inventory/main.py --generate-config
Example Config
```
vm_rule_set: vm_default
label_rule_set: label_default
attribute_rule_sets:
  - name: port_group
    attribute: SSH_PORT
    prefix: port_
    value_rules: []
  - name: role_group
    attribute: ROLE
    prefix: role_
    value_rules:
      - pattern: ^db
        replacement: database
      - pattern: '[\-\.]'
        replacement: _
sanitization_rules:
  vm_default:
    prefix: vm_
    name_rules:
      - pattern: ^([a-zA-Z]+)\..*
        replacement: $1
      - pattern: [-0-9].*
        replacement: ""
      - pattern: '-'
        replacement: _
  label_default:
    prefix: label_
    name_rules:
      - pattern: '[\-\.]'
        replacement: _
  vm_db:
    prefix: db_
    name_rules:
      - pattern: ^([a-zA-Z0-9]+)-.*
        replacement: $1
      - pattern: _+
        replacement: _
servers:
  - endpoint: http://your-opennebula-server
    port: 2633
    user: your_username
    password: your_password
```
## Configuration Options
* vm_rule_set: Rule set for VM names (e.g., vm_default).
* label_rule_set: Rule set for labels (e.g., label_default).
* attribute_rule_sets: List of rules for attribute-based grouping (e.g., SSH_PORT, ROLE).
    * name: Unique rule set name.
    * attribute: Attribute key (e.g., SSH_PORT).
    * prefix: Group prefix (e.g., port_).
    * value_rules: Regex rules for attribute values.
* sanitization_rules: Named rule sets for VM names and labels.
    * prefix: Group prefix.
    * name_rules: List of regex patterns and replacements.
* servers: List of OpenNebula servers.
    * endpoint: Server URL.
    * port: RPC port.
    * user: Username.
    * password: Password.
## Grouping Examples
    * VM Names: app1-prod-01.db.example → vm_app1 (with vm_default).
    * Labels: dba,sysops → label_dba, label_sysops (with label_default).
    * Attributes: SSH_PORT=22 → port_22, ROLE=db.admin → role_database_admin.
## Usage
Test the inventory:
```
ansible-inventory -i ~/.ansible/collections/ansible_collections/sysops/opennebula_inventory/plugins/inventory/main.py --list
```
Run Ansible:
```
ansible -i ~/.ansible/collections/ansible_collections/sysops/opennebula_inventory/plugins/inventory/main.py all -m ping
```
## Requirements
```
pyone
pyyaml
```
### Install:

```
pip install -r ~/.ansible/collections/ansible_collections/sysops/opennebula_inventory/requirements.txt
```
## License
GPL-3.0-or-later