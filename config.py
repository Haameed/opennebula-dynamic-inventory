import os
import sys
import json
from typing import List

class Config:
    def __init__(self, url: str, port: int,  user: str, password: str):
        self.url = url
        self.user = user
        self.password = password
        self.port = port
        self.endpoint = f"{self.url}:{self.port}/RPC2"

def load_config(config_path: str = None) -> List[Config]:
    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "config.json")

    try:
        with open(config_path, "r") as file:
            config_data = json.load(file)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {config_path}: {e}")
        sys.exit(1)

    if not isinstance(config_data, list):
        print("Config file must contain a list of server configurations")
        sys.exit(1)

    configs = []
    for idx, server in enumerate(config_data, 1):
        url = server.get("endpoint")
        port = server.get("port")
        user = server.get("user")
        password = server.get("password")
        endpoint = f"{url}:{port}/RPC2"

        if not all([url, user, password, port]):
            print(f"Server configuration {idx} missing required fields: endpoint, user, password or port")
            sys.exit(1)

        configs.append(Config(url, port, user, password))

    if not configs:
        print("Config file must contain at least one valid server configuration")
        sys.exit(1)

    return configs