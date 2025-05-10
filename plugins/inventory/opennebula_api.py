from dataclasses import dataclass
import xmlrpc.client
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text

try:
    import pyone
except ImportError:
    raise AnsibleError("The 'pyone' module is required for this inventory plugin")

@dataclass
class VirtualMachine:
    vm_name: str
    ip_address: str
    port: int
    labels: str
    attributes: dict

def get_all_vms(server_config):
    """Fetch all VMs from an OpenNebula server."""
    try:
        endpoint = f"{server_config['endpoint']}:{server_config.get('port', 2633)}"
        session = f"{server_config['user']}:{server_config['password']}"
        one = pyone.OneServer(endpoint, session=session)

        vms = []
        for vm in one.vmpool.infoextended(-2, -1, -1, -1):  
            ip_address = None
            for nic in vm.TEMPLATE.get('NIC', []):
                if nic.get('IP'):
                    ip_address = nic['IP']
                    break
            if not ip_address:
                continue  # Skip VMs without IP

            attributes = {
                k: v for k, v in vm.TEMPLATE.items()
                if isinstance(v, str) and k not in ('NIC', 'DISK', 'CONTEXT')
            }
            port = int(attributes.get('SSH_PORT', 22))

            vms.append(VirtualMachine(
                vm_name=vm.NAME,
                ip_address=ip_address,
                port=port,
                labels=vm.LABELS if hasattr(vm, 'LABELS') else '',
                attributes=attributes
            ))
        return vms
    except Exception as e:
        raise AnsibleError(f"Failed to fetch VMs from {server_config['endpoint']}: {to_text(e)}")