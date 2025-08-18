from typing import Dict, Any
import yaml

class RepliesManager:
    _instance = None
    templates: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_replies()
        return cls._instance

    @classmethod
    def _load_replies(cls) -> None:
        file = open("data/replies.yaml", "r", encoding="utf-8")
        cls.templates = yaml.safe_load(file)
        file.close()

    @classmethod
    def get(cls, key: str, **kwargs) -> str:
        return cls.templates[key].format(**kwargs)