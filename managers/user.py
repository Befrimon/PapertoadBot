from dataclasses import dataclass

@dataclass
class User:
    status: str
    ask_ban: bool
    # User info
    user_id: int
    date_joined: str
    action_count: int
    # Char info
    char_name: str
    char_race: str
    char_class: str

    action: bool
    skills: list[str]
    inventory: list[str]

