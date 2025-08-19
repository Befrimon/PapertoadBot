from dacite import from_dict
from dataclasses import asdict
import json
import logging
import threading
import time
from typing import Dict, Any

from managers.user import User

class UserManager:
    _instance = None
    user_data: Dict[int, User] = {}
    skill_list: Dict[str, Dict[str, Any]] = {}
    item_list: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_data()
            cls._start_autosave()
        return cls._instance

    @classmethod
    def _load_data(cls):
        file = open("data/user_data.json", "r", encoding="utf-8")
        raw_users = json.load(file)
        file.close()

        for key in raw_users:
            cls.user_data[int(key)] = from_dict(data_class=User, data=raw_users[key])

        ## Load skills
        file = open("data/skills.json", "r", encoding="utf-8")
        cls.skill_list = json.load(file)
        file.close()

        ## Load items
        file = open("data/items.json", "r", encoding="utf-8")
        cls.item_list = json.load(file)
        file.close()

    @classmethod
    def reload_data(cls):
        cls._save()
        cls._load_data()

    @classmethod
    def get_user(cls, user_id: int):
        return cls.user_data[user_id]

    @classmethod
    def user_list(cls):
        return cls.user_data.keys()

    @classmethod
    def create(cls, **kwargs):
        cls.user_data[kwargs["user_id"]] = User(status="await", **kwargs)
        cls._save()

    @classmethod
    def approve_user(cls, user_id: int):
        cls.user_data[user_id].status = "active"
        cls.user_data[user_id].action = True

    @classmethod
    def reject_user(cls, user_id: int):
        cls.user_data.pop(user_id)

    @classmethod
    def do_action(cls, user_id: int):
        cls.user_data[user_id].action = False
        cls.user_data[user_id].action_count += 1

    @classmethod
    def reject_action(cls, user_id: int):
        cls.user_data[user_id].action = True
        cls.user_data[user_id].action_count -= 1

    @classmethod
    def ban_ask(cls, user_id: int):
        cls.user_data[user_id].ask_ban = True

    @classmethod
    def unban_ask(cls, user_id):
        cls.user_data[user_id].ask_ban = False

    #region Skills
    @classmethod
    def add_skill(cls, user_id: int, skill_id: str) -> bool:
        if skill_id in cls.user_data[user_id].skills:
            return False
        cls.user_data[user_id].skills.append(skill_id)
        return True

    @classmethod
    def get_skill_name(cls, skill_id: str):
        return cls.skill_list[skill_id]["name"]

    @classmethod
    def get_skill(cls, skill_id: str):
        return cls.skill_list[skill_id]

    @classmethod
    def get_item(cls, item_id: str):
        return cls.item_list[item_id]

    #endregion

    #region Autosave
    _autosave = False
    _as_thread = None

    @classmethod
    def _start_autosave(cls):
        if cls._autosave:
            return
        cls._autosave = True
        cls._as_thread = threading.Thread(target=cls._autosave_loop, daemon=True)
        cls._as_thread.start()
        logging.log(logging.INFO, "Autosave enabled!")

    @classmethod
    def _autosave_loop(cls):
        while cls._autosave:
            time.sleep(3600)  # One hour
            cls._save()

    @classmethod
    def _save(cls):
        ready_data = {}
        for key in cls.user_data:
            ready_data[key] = asdict(cls.user_data[key])
        file = open("data/user_data.json", "w", encoding="utf-8")
        json.dump(ready_data, file, indent=2)
        file.close()
        logging.log(logging.INFO, "User data saved!")

    @classmethod
    def _stop_autosave(cls):
        if not cls._autosave:
            return
        cls._autosave = False
        if cls._as_thread is not None:
            cls._as_thread.join()
        cls._save()
        logging.log(logging.INFO, "Autosave disabled!")
    #endregion
