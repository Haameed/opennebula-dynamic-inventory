#!/usr/bin/env python

import os
import yaml
import sys

def generate_config(output_dir='.'):
    """Generate a sample opennebula.yaml configuration file."""
    config = {
        'vm_rule_set': 'vm_default',
        'label_rule_set': 'label_default',
        'attribute_rule_sets': [
            {
                'name': 'port_group',
                'attribute': 'SSH_PORT',
                'prefix': 'port_',
                'value_rules': []
            },
            {
                'name': 'role_group',
                'attribute': 'ROLE',
                'prefix': 'role_',
                'value_rules': [
                    {'pattern': '^db', 'replacement': 'database'},
                    {'pattern': '[\\-\\.]', 'replacement': '_'}
                ]
            }
        ],
        'sanitization_rules': {
            'vm_default': {
                'prefix': 'vm_',
                'name_rules': [
                    {'pattern': '^([a-zA-Z]+)\\..*', 'replacement': '$1'},
                    {'pattern': '[-0-9].*', 'replacement': ''},
                    {'pattern': '-', 'replacement': '_'}
                ]
            },
            'label_default': {
                'prefix': 'label_',
                'name_rules': [
                    {'pattern': '[\\-\\.]', 'replacement': '_'}
                ]
            },
            'vm_db': {
                'prefix': 'db_',
                'name_rules': [
                    {'pattern': '^([a-zA-Z0-9]+)-.*', 'replacement': '$1'},
                    {'pattern': '_+', 'replacement': '_'}
                ]
            }
        },
        'servers': [
            {
                'endpoint': 'http://your-opennebula-server',
                'port': 2633,
                'user': 'your_username',
                'password': 'your_password'
            }
        ]
    }

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'opennebula.yaml')
    with open(output_path, 'w') as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    print(f"Sample configuration generated at {output_path}")

if __name__ == '__main__':
    generate_config()