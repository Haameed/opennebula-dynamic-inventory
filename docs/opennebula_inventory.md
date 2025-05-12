# OpenNebula Inventory Plugin

The `snapp.opennebula` inventory plugin dynamically fetches virtual machines (VMs) from OpenNebula servers and organizes them into groups based on VM names, labels, and attributes (e.g., `SSH_PORT`). It supports regex-based sanitization for group names and is designed for use with Ansible CLI, AWX, and GitLab CI.

## Overview
- **Namespace**: `snapp`
- **Name**: `opennebula`
- **Version**: 1.0.0
- **Plugin Type**: Inventory
- **Repository**: `https://gitlab.snapp.ir/sysops/opennebula_inventory`

This plugin connects to OpenNebula servers, retrieves running VMs, and creates inventory groups such as `vm_teleport`, `label_dba`, and `port_22`. It’s ideal for managing OpenNebula-based infrastructure with Ansible.

## Requirements
- **Ansible**: 2.9 or later
- **Python**: 3.7+ (tested with 3.13)
- **Dependencies**:
  - `pyone`: OpenNebula Python SDK
  - `pyyaml`: YAML parsing
  Install with:
  ```bash
  pip install pyone pyyaml
  ```
- **OpenNebula**: Access to servers (e.g., `http://one.snapp.tech:2633/RPC2`)

## Installation
Install the `snapp.opennebula` collection using `ansible-galaxy`:

```bash
ansible-galaxy collection install git+https://gitlab.snapp.ir/sysops/opennebula_inventory.git --force
```

For private repositories, include a GitLab Personal Access Token (PAT):

```bash
ansible-galaxy collection install git+https://<username>:<PAT>@gitlab.snapp.ir/sysops/opennebula_inventory.git --force
```

The collection installs to `~/.ansible/collections/ansible_collections/snapp/opennebula`.

## Configuration
The plugin requires two configuration files: `inventory.yaml` and `opennebula.yaml`.

### `inventory.yaml`
Define the plugin and its configuration file:

```yaml
plugin: snapp.opennebula
config_path: ./opennebula.yaml
```

Example:
```bash
mkdir -p /path/to/project
cat > /path/to/project/inventory.yaml << EOL
plugin: snapp.opennebula
config_path: ./opennebula.yaml
EOL
```

### `opennebula.yaml`
Generate a sample configuration file:

```bash
python ~/.ansible/collections/ansible_collections/snapp/opennebula/plugins/inventory/opennebula.py --generate-config
```

This creates `opennebula.yaml`:

```yaml
vm_rule_set: vm_default
label_rule_set: label_default
attribute_rule_sets:
- attribute: SSH_PORT
  name: port_group
  prefix: port_
  value_rules: []
sanitization_rules:
  vm_default:
    prefix: vm_
    name_rules:
    - pattern: '^([^.]+).*'
      replacement: \1
    - pattern: -\d+$
      replacement: ''
    - pattern: '-'
      replacement: _
  label_default:
    prefix: label_
    name_rules:
    - pattern: '[\-\.]'
      replacement: _
servers:
- endpoint: http://your-first-opennebula-server
  password: yourpassword
  port: 2633
  user: yourusername
- endpoint: http://your-second-opennebula-server
  password: yourpassword
  port: 2633
  user: yourusername
```

Edit `opennebula.yaml` to include your server details:

```yaml
servers:
  - endpoint: http://one.snapp.tech
    password: your_password
    port: 2633
    user: your_username
  - endpoint: http://new-one.snapp.tech
    password: your_password
    port: 2633
    user: your_username
```

### `ansible.cfg`
Configure Ansible to use the collection:

```ini
[defaults]
collections_paths = ~/.ansible/collections:/usr/share/ansible/collections
inventory = ./inventory.yaml

[inventory]
enable_plugins = snapp.opennebula
```

Example:
```bash
cat > /path/to/project/ansible.cfg << EOL
[defaults]
collections_paths = ~/.ansible/collections:/usr/share/ansible/collections
inventory = ./inventory.yaml

[inventory]
enable_plugins = snapp.opennebula
EOL
```

## Features

### VM Grouping
VM names are sanitized using regex rules defined in `sanitization_rules.vm_default`. Example:
- `teleport-audit-02.db.asia.snapp.infra` → `vm_teleport_audit`
- `automation.tools.afra.snapp.infra` → `vm_automation`

Rules:
```yaml
sanitization_rules:
  vm_default:
    prefix: vm_
    name_rules:
    - pattern: '^([^.]+).*'
      replacement: \1
    - pattern: -\d+$
      replacement: ''
    - pattern: '-'
      replacement: _
```

### Label Grouping
Labels from `USER_TEMPLATE['LABELS']` are sanitized to create groups (e.g., `label_dba_prod`).

Rules:
```yaml
sanitization_rules:
  label_default:
    prefix: label_
    name_rules:
    - pattern: '[\-\.]'
      replacement: _
```

### SSH_PORT Attribute Support
The plugin extracts `SSH_PORT` from `USER_TEMPLATE` to:
- Set `ansible_port` for each VM (default: `22`).
- Create groups like `port_22` or `port_2222`.

Configuration:
```yaml
attribute_rule_sets:
  - attribute: SSH_PORT
    name: port_group
    prefix: port_
    value_rules: []
```

Example:
- VM: `teleport-01.db.asia.snapp.infra`
- `USER_TEMPLATE['SSH_PORT']`: `2222`
- Result:
  - Host variables: `ansible_host: <ip>, ansible_port: 2222`
  - Group: `port_2222`

## Usage

### View Inventory
List the inventory:

```bash
ansible-inventory -i inventory.yaml --list -vvv > inventory.log
```

Check `inventory.log` for groups (`vm_`, `label_`, `port_`) and host variables.

### Run Playbook
Create a test playbook (`test.yml`):

```yaml
- name: Test OpenNebula Inventory
  hosts: all
  tasks:
    - name: Ping all hosts
      ansible.builtin.ping:
```

Run:
```bash
ansible-playbook -i inventory.yaml test.yml
```

Limit to a group:
```bash
ansible-playbook -i inventory.yaml test.yml -l vm_teleport
```

## Troubleshooting
- **No VMs**:
  - Verify server credentials in `opennebula.yaml`.
  - Ensure VMs are in `RUNNING` state (state `3`).
  - Test connectivity: `curl http://one.snapp.tech:2633/RPC2`.
- **Grouping Issues**:
  - Check `inventory.log` for warnings (e.g., `No valid VM group for <vm_name>`).
  - Adjust `sanitization_rules` for VM names or labels.
- **SSH_PORT Missing**:
  - Ensure `SSH_PORT` is set in `USER_TEMPLATE`.
  - Verify `attribute_rule_sets` configuration.
- **Installation Issues**:
  - Check GitLab PAT for private repository access.
  - Ensure `pyone` and `pyyaml` are installed.

## Support
File issues at `https://gitlab.snapp.ir/sysops/opennebula_inventory` or contact the Snapp SysOps team.