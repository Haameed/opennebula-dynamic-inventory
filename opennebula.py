import pyone
import logging
from typing import List
from inventory import VirtualMachine
from utils import verify_ip_address

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
        if  vm_state == 3:
            labels = vm.USER_TEMPLATE.get("LABELS", "")
            portlabel = vm.USER_TEMPLATE.get("SSH_PORT", "22")
            if type(portlabel) is int:
                vmport = portlabel
            else: 
                vmport = int(portlabel)
            nics = vm.TEMPLATE.get("NIC", [])
            if type(nics) is list:
                for nic in nics:
                    ip_address = nic.get("IP", "")
                    if ip_address and verify_ip_address(ip_address):
                        with lock: 
                            vm_list.append(VirtualMachine(vm_name, ip_address, vmport, labels))
                        break
            else:
                ip_address = nics.get("IP", "")

                with lock: 
                    vm_list.append(VirtualMachine(vm_name, ip_address, vmport, labels))
            
    except Exception as e:
        logging.error(f"Error processing VM ID {vm.ID}: {e}")
