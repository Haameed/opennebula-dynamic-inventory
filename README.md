# Sysops OpenNebula Inventory Collection

This Ansible collection provides a dynamic inventory plugin for OpenNebula, enabling grouping of virtual machines (VMs) by names, labels, and attributes (e.g., `SSH_PORT`, `ROLE`) using a YAML configuration.

## Features
- Fetches VMs from one or more OpenNebula servers.
- Groups VMs dynamically based on:
  - VM names (e.g., `vm_app1`).
  - Labels (e.g., `label_dba`, `label_sysops`).
  - Attributes (e.g., `port_22`, `role_database`).
- Supports regex-based sanitization for group names.
- Generates a sample `config.yaml` with `--generate-config`.

## Requirements
- Ansible 2.9+
- Python 3.6+
- `pyone` (`pip install pyone`)
- `pyyaml` (`pip install pyyaml`)

## Installation
Install from Ansible Galaxy:
```bash
ansible-galaxy collection install sysops.opennebula_inventory
```

Or from Git:
```bash
ansible-galaxy collection install git+https://github.com/your_username/opennebula_inventory.git
```

Install Python dependencies:
```bash
pip install -r ~/.ansible/collections/ansible_collections/sysops/opennebula_inventory/requirements.txt
```

## Setup
1. Configure Ansible to use the inventory plugin by adding to `ansible.cfg`:
   ```ini
   [defaults]
   inventory = sysops.opennebula
   host_key_checking = False
   timeout = 10
   retry_files_enabled = False

   [inventory]
   enable_plugins = sysops.opennebula

   [ssh_connection]
   pipelining = True
   ```

2. Generate a sample configuration:
   ```bash
   ~/.ansible/collections/ansible_collections/sysops/opennebula_inventory/plugins/inventory/opennebula.py --generate-config
   ```

3. Edit `dynamic_inventory/config.yaml`:
   - Replace placeholder server details (`endpoint`, `user`, `password`) with your OpenNebula credentials.
   - Customize grouping rules as needed (see Configuration).

## Usage
Test the inventory:
```bash
ansible-inventory -i sysops.opennebula --list
```

Run Ansible commands:
```bash
ansible -i sysops.opennebula all -m ping
ansible-playbook -i sysops.opennebula playbook.yml
```

## Configuration
The plugin uses a YAML configuration file (`dynamic_inventory/config.yaml`) to define grouping rules.

### Sample `config.yaml`
```yaml
# Configuration for OpenNebula Ansible inventory plugin
vm_rule_set: vm_default
label_rule_set: label_default

# Attribute-based grouping rules
attribute_rule_sets:
  - name: port_group
    attribute: SSH_PORT
    prefix: port_
    value_rules: []
    # Groups VMs by SSH_PORT (e.g., port_22 for SSH_PORT=22)
  - name: role_group
    attribute: ROLE
    prefix: role_
    value_rules:
      - pattern: ^db
        replacement: database
        # Replace 'db' with 'database'
      - pattern: '[\-\.]'
        replacement: _
        # Replace hyphens or dots with underscores

# Rule sets for VM names and labels
sanitization_rules:
  vm_default:
    prefix: vm_
    name_rules:
      - pattern: ^([a-zA-Z]+)\..*
        replacement: $1
        # Extract prefix before dot
      - pattern: [-0-9].*
        replacement: ""
        # Remove number suffixes
      - pattern: '-'
        replacement: _
        # Replace hyphens with underscores
  label_default:
    prefix: label_
    name_rules:
      - pattern: '[\-\.]'
        replacement: _
        # Replace hyphens or dots with underscores
  vm_db:
    prefix: db_
    name_rules:
      - pattern: ^([a-zA-Z0-9]+)-.*
        replacement: $1
        # Extract prefix before hyphen
      - pattern: _+
        replacement: _
        # Normalize multiple underscores

# OpenNebula server configurations
servers:
  - endpoint: http://your-opennebula-server
    port: 2633
    user: your_username
    password: your_password
```

### Configuration Options
- **`vm_rule_set`**: Specifies the rule set for VM names (e.g., `vm_default`).
- **`label_rule_set`**: Specifies the rule set for labels (e.g., `label_default`).
- **`attribute_rule_sets`**: Defines rules for grouping by VM attributes.
  - `name`: Unique rule set name.
  - `attribute`: Attribute key (e.g., `SSH_PORT`, `ROLE`).
  - `prefix`: Group prefix (e.g., `port_`, `role_`).
  - `value_rules`: Optional regex patterns for attribute values.
- **`sanitization_rules`**: Defines rule sets for VM names and labels.
  - `prefix`: Prefix for group names.
  - `name_rules`: List of regex patterns and replacements.
- **`servers`**: List of OpenNebula server configurations.
  - `endpoint`: Server URL.
  - `port`: RPC port.
  - `user`: Username.
  - `password`: Password.

### Example Grouping
- **VM Name**: `app1-prod-01.db.example` → `vm_app1` (with `vm_default`).
- **Labels**: `dba,sysops` → `label_dba`, `label_sysops` (with `label_default`).
- **Attributes**:
  - `SSH_PORT=22` → `port_22`.
  - `ROLE=db.admin` → `role_database_admin`.

### Custom Rule Example
Add a rule set for environment-based grouping:
```yaml
attribute_rule_sets:
  - name: env_group
    attribute: ENV
    prefix: env_
    value_rules:
      - pattern: ^prod
        replacement: production
        # Replace 'prod' with 'production'
sanitization_rules:
  vm_app:
    prefix: app_
    name_rules:
      - pattern: ^app
        replacement: application
        # Replace 'app' with 'application'
      - pattern: \..*
        replacement: ""
        # Remove suffix after dot
```

## Testing
1. Generate and edit `config.yaml`.
2. Test inventory:
   ```bash
   ansible-inventory -i sysops.opennebula --list
   ```
3. Run a test playbook:
   ```bash
   ansible-playbook -i sysops.opennebula tests/test.yml
   ```

## Contributing
- Report issues or submit pull requests at: https://github.com/your_username/opennebula_inventory
- Follow the coding style in existing scripts.
- Add tests in `tests/` for new features.

## License
GPL-3.0-or-later