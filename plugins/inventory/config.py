import yaml
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text

def load_config(config_path):
    """Load and validate the YAML configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        raise AnsibleError(f"Failed to load configuration {config_path}: {to_text(e)}")

    # Validate required fields
    if not config.get('servers'):
        raise AnsibleError("Configuration must include at least one server")

    return config