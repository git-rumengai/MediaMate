import yaml
from typing import Optional


class XpathParser:
    def __init__(self, yaml_path: str):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f)

    def get_xpath(self, path: str) -> Optional[str]:
        keys = path.split()
        node = self.data
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return None
        return node.get('xpath') if isinstance(node, dict) else None
