# Snapp OpenNebula Ansible Inventory Plugin

The `snapp.opennebula` Ansible inventory plugin dynamically fetches virtual machines (VMs) from OpenNebula servers and groups them by VM names, labels, and attributes (e.g., `SSH_PORT`). It supports regex-based name sanitization and generates a sample configuration file for easy setup.

This plugin is designed for use with Ansible CLI, AWX, and GitLab CI, and is compatible with OpenNebula servers at `http://one.snapp.tech` and `http://new-one.snapp.tech`.

## Features
- Fetches only running VMs (state `RUNNING`) from OpenNebula.
- Groups VMs by sanitized names (e.g., `vm_teleport`, `vm_teleport_audit`).
- Supports label-based grouping (e.g., `label_dba`).
- Supports attribute-based grouping, including `SSH_PORT` (e.g., `port_22`).
- Configurable via `opennebula.yaml` with regex sanitization rules.
- Generates a sample configuration file with `--generate-config`.

## Prerequisites
- **Python 3.13**: Ensure Python 3.13 is installed (e.g., `/opt/homebrew/opt/python@3.13/bin/python3.13`).
- **Ansible**: Install Ansible (e.g., `pip install ansible`).
- **Dependencies**: Install `pyone` and `pyyaml`:
```
 python3 -m pip install pyone pyyaml
```
- **Git**: Required for installing the collection.
- **Access**: Ensure access to OpenNebula servers and the Git repository.

## Installation

### Install the Collection Using Git
The `snapp.opennebula` collection is hosted at `git@gitlab.snapp.ir:sysops/opennebula_inventory.git`. Install it using `ansible-galaxy`:

```

ansible-galaxy collection install git@gitlab.snapp.ir:sysops/opennebula_inventory.git --force
```
or create a file named requirements.yml with below content.
```yaml
collections:
  - name: git@gitlab.snapp.ir:sysops/opennebula_inventory.git
    type: git
    version: main
```
then run: 
```bash
ansible-galaxy collection install -r requirements.yml --force

```

The collection will be installed to `~/.ansible/collections/ansible_collections/snapp/opennebula`.

To update the collection, re-run the command with `--force`.

## Configuration

### Configure inventory
Create an `opennebula.yaml` file in your inventory path and specify the configuration as below:

```yaml
plugin: snapp.opennebula.opennebula
attribute_rule_sets:
- name: port_group
  attribute: SSH_PORT
  prefix: port_
  value_rules: []
sanitization_rules:
  vm_default:
    prefix: vm_
    name_rules:
    - pattern: '^([^.]+).*'
      replacement:  '\1'
    - pattern: -\d+$
      replacement: ""
    - pattern: "-"
      replacement: "_"
  label_default:
    prefix: label_
    name_rules:
    - pattern: '[\-\.\ ]'
      replacement: _
servers:
- endpoint: http://first-opennebula-server
  port: 2633
  user: yourusername
  password: yourpassword    
- endpoint: http://second-opennebula-server
  port: 2633
  user: yourusername
  password: yourpassword
```

### Generate Configuration File (`opennebula.yaml`)
The plugin can generate a sample `opennebula.yaml` configuration file with default settings.

Run the following command to generate `opennebula.yaml` in your working directory:

```bash
python3 ~/.ansible/collections/ansible_collections/snapp/opennebula/plugins/inventory/opennebula.py --generate-config
```

This creates `opennebula.yaml` with the following structure:

```yaml
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

Edit `opennebula.yaml` to include your OpenNebula server details:

```bash
vi opennebula.yaml
```

Update the `servers` section with your server endpoints, usernames, and passwords:


The configuration supports:
- **VM Grouping**: Sanitizes VM names (e.g., `teleport-audit-02.db.asia.snapp.infra` → `vm_teleport_audit`).
- **Label Grouping**: Sanitizes labels (e.g., `dba-prod` → `label_dba_prod`).
- **Attribute Grouping**: Groups by attributes like `SSH_PORT` (e.g., `port_22`).
### Ansible configuration (Optional)
You can configure your ansible to use a directory as inventory source. this directory should contain at least one invntory (dynamic/static).
here is an example of having two static and dynamic inventory alongside eachother.
Create a file named `ansible.cfg` in your working directory.
```
[defaults]
inventory = ./inventory/
```
Then put your inventories in a directory named inventory.
```
inventory/
 --- inventory.yml # a clasic yaml inventory.
 --- opennebula.yaml 
```
Finally run:
```
ansible-inventory --list 
```
## SSH_PORT Attribute Support
The plugin supports the `SSH_PORT` attribute to configure the SSH port for each VM. This is extracted from the VM’s `USER_TEMPLATE` in OpenNebula, with a default of `22` if not specified.

### How It Works
- The plugin checks `vm.USER_TEMPLATE['SSH_PORT']` for each VM.
- The `SSH_PORT` value is used to:
  - Set the `ansible_port` variable for the VM (e.g., `ansible_port: 2222`).
  - Create attribute-based groups (e.g., `port_2222` for VMs with `SSH_PORT=2222`).
- Configuration in `opennebula.yaml`:
  ```yaml
  attribute_rule_sets:
    - attribute: SSH_PORT
      name: port_group
      prefix: port_
      value_rules: []
  ```
  - `attribute`: Specifies `SSH_PORT` as the attribute to process.
  - `name`: Names the group rule (`port_group`).
  - `prefix`: Adds `port_` to group names (e.g., `port_22`).
  - `value_rules`: Optional regex rules for sanitizing `SSH_PORT` values (empty by default).

### Example
For a VM with:
- Name: `teleport-01.db.asia.snapp.infra`
- IP: `192.168.1.10`
- `USER_TEMPLATE['SSH_PORT']`: `2222`

The plugin:
- Sets host variables:
  ```yaml
  teleport-01.db.asia.snapp.infra:
    ansible_host: 192.168.1.10
    ansible_port: 2222
  ```
- Adds the VM to the `port_2222` group.

## Running the Collection

### Using `ansible-inventory`
To view the inventory generated by the plugin:

```bash
ansible-inventory -i inventory.yaml --list 
```

- `-i inventory.yaml`: Specifies the inventory file.
- `--list`: Outputs the full inventory in JSON format.

Check `inventory.log` for:
- VM groups (e.g., `vm_teleport`, `vm_teleport_audit`, `vm_automation`).
- Label groups (e.g., `label_dba`).
- Attribute groups (e.g., `port_22`, `port_2222`).
- Host variables (`ansible_host`, `ansible_port`).

Example output snippet:
```json
{
  "all": {
    "children": [
      "vm_teleport",
      "vm_teleport_audit",
      "port_22"
    ]
  },
  "vm_teleport": {
    "hosts": [
      "teleport-01.db.asia.snapp.infra",
      "teleport-02.db.asia.snapp.infra"
    ]
  },
  "port_22": {
    "hosts": [
      "teleport-01.db.asia.snapp.infra"
    ]
  },
  "_meta": {
    "hostvars": {
      "teleport-01.db.asia.snapp.infra": {
        "ansible_host": "192.168.1.10",
        "ansible_port": 22
      }
    }
  }
}
```

### Using `ansible-playbook`
To run a playbook using the inventory:

1. Create a test playbook (e.g., `test.yml`):
   ```yaml
   - name: Test OpenNebula Inventory
     hosts: all
     tasks:
       - name: Ping all hosts
         ansible.builtin.ping:
   ```

   Save it:
   ```bash
   cat > test.yml << EOL
   - name: Test OpenNebula Inventory
     hosts: all
     tasks:
       - name: Ping all hosts
         ansible.builtin.ping:
   EOL
   ```

2. Run the playbook:
   ```bash
   ansible-playbook -i inventory.yaml test.yml
   ```

   This pings all VMs in the inventory, using their `ansible_host` and `ansible_port` variables.

3. Run against specific groups:
   ```bash
   ansible-playbook -i inventory.yaml test.yml -l vm_teleport
   ```
   The `-l vm_teleport` limits the playbook to the `vm_teleport` group.

## Troubleshooting
- **No VMs in Inventory**:
  - Check `opennebula.yaml` for correct server endpoints, usernames, and passwords.
  - Ensure VMs are in the `RUNNING` state (state `3`).
  - Verify `pyone` can connect: `curl http://one.snapp.tech:2633/RPC2`.
- **Invalid Groups**:
  - Use -vvv to see debug output for warnings and infos (e.g., `No valid VM group for <vm_name>`).
  - Adjust `sanitization_rules` in `opennebula.yaml` if VM names are incorrectly grouped.
- **Missing `SSH_PORT` Groups**:
  - Ensure `SSH_PORT` is set in `USER_TEMPLATE` for VMs in OpenNebula.
  - Verify `attribute_rule_sets` in `opennebula.yaml`.
- **GitLab Access Issues**:
  - Ensure your PAT is valid and has repository access.
  - Test with `git clone git@gitlab.snapp.ir:sysops/opennebula_inventory.git`.

## Support
For issues, contact the Snapp SysOps team or open an issue in the GitLab repository: `https://gitlab.snapp.ir/sysops/opennebula_inventory`.