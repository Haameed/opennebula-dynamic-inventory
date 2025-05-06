import json
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import List
from config import load_config
from opennebula import fetch_vms
from inventory import VirtualMachine, create_inventory
from ansible.errors import AnsibleError
import sys

try:
    import pyone

    HAS_PYONE = True
except ImportError:
    HAS_PYONE = False

def main():
    if not HAS_PYONE:
        raise AnsibleError('OpenNebula Inventory plugin requires pyone to work!')
    cfg = load_config()

    virtual_machines = []

    lock = Lock()
    with ThreadPoolExecutor() as executor:
        executor.map(
            lambda cfg: fetch_vms(cfg.user, cfg.password, cfg.endpoint, virtual_machines, lock),
            cfg,
    )
    unique_vms_dict = {}
    for vm in virtual_machines:
        if vm.vm_name not in unique_vms_dict:
            unique_vms_dict[vm.vm_name] = vm

    unique_vms = list(unique_vms_dict.values())
    inv = create_inventory(unique_vms)

    try:
        print(json.dumps(inv, indent=2))
    except json.JSONDecodeError as e:
        logging.error(f"Error serializing inventory to JSON: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        main()
    elif len(sys.argv) > 2 and sys.argv[1] == "--host":
        print(json.dumps({}))  # Return empty dict as _meta.hostvars is used
    else:
        print("Usage: main.py --list")
        sys.exit(1)