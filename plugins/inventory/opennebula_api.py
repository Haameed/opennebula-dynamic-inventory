import pyone
import logging
from typing import List
from inventory import VirtualMachine
# from utils import verify_ip_address

def fetch_vms(user: str, password: str, endpoint: str, vm_list: List[VirtualMachine], lock) -> None:
    try:
        client = pyone.OneServer(endpoint, session=f"{user}:{password}")
        vm_pool = client.vmpool.infoextended(-2, -1, -1, -1) 
        for vm in vm_pool.VM:
            process_vm(vm, vm_list, lock)
    except Exception as e:
        logging.error(f"Error fetching VMs from endpoint {endpoint}: {e}")

def process_vm(vm, vm_list: List[VirtualMachine], lock) -> None:
    try:
        vm_name = vm.NAME.strip()
        vm_state = vm.STATE         
        if vm_state == 3:
            labels = vm.USER_TEMPLATE.get("LABELS", "")
            portlabel = vm.USER_TEMPLATE.get("SSH_PORT", "22")
            try:
                vmport = int(portlabel)
                if not (1 <= vmport <= 65535):
                    logging.warning(f"Invalid SSH_PORT {portlabel} for VM {vm_name}, using default 22")
                    vmport = 22
            except ValueError:
                logging.warning(f"Invalid SSH_PORT {portlabel} for VM {vm_name}, using default 22")
                vmport = 22            
            attributes = {k: str(v) for k, v in vm.USER_TEMPLATE.items()}
            for key in ["CPU", "MEMORY"]:
                if key in vm.TEMPLATE:
                    attributes[key] = str(vm.TEMPLATE[key])

            nics = vm.TEMPLATE.get("NIC", [])
            if isinstance(nics, list):
                # for nic in nics:
                first_nic = nics[0]
                ip_address = first_nic.get("IP", "")
                    # if ip_address and verify_ip_address(ip_address):
                with lock: 
                    vm_list.append(VirtualMachine(vm_name, ip_address, vmport, labels, attributes))
                        # break
            elif isinstance(nics, dict):
                ip_address = nics.get("IP", "")
                # if ip_address and verify_ip_address(ip_address):
                with lock: 
                    vm_list.append(VirtualMachine(vm_name, ip_address, vmport, labels, attributes))
    except Exception as e:
        logging.error(f"Error processing VM ID {vm.ID}: {e}")