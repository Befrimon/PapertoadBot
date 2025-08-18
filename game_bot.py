import asyncio
import datetime
import logging

import dotenv
from enum import Enum
import os

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from managers.replies_manager import RepliesManager
from managers.user_manager import UserManager

class AwaitStatus(Enum):
    INFO = 0
    RACE = 1
    CLASS = 2
    DESCRIPTION = 3
    ACTION = 4
    ASK = 5

class GameBot:
    dp = Dispatcher()
    router = Router()
    bot: Bot = None
    await_messages: dict[int, dict] = {}
    skill_pages: dict[int, int] = {}
    inventory_pages: dict[int, int] = {}
    gm_id = 0

    def __new__(cls):
        RepliesManager()
        UserManager()

        dotenv.load_dotenv()
        cls.gm_id = int(os.getenv("PTB_GM_ID"))
        bot_token = os.getenv("PTB_TOKEN")
        if not (cls.gm_id and bot_token):
            raise EnvironmentError("Отсутствуют необходимые переменные")

        cls.bot = Bot(bot_token)
        cls.dp.include_router(cls.router)
        asyncio.run(cls.dp.start_polling(cls.bot))

    @classmethod
    def get_bot(cls) -> Bot:
        return cls.bot

    #region Router
    @staticmethod
    @router.callback_query(lambda c: c.data == "skill_back")
    async def skill_back(callback: CallbackQuery) -> None:
        user_id = callback.from_user.id
        user = UserManager.get_user(user_id)
        if len(user.skills) == 1:
            return
        if GameBot.skill_pages[user_id] != 0:
            GameBot.skill_pages[user_id] -= 1
        else:
            GameBot.skill_pages[user_id] = len(user.skills)-1

        skill = UserManager.get_skill(user.skills[GameBot.skill_pages[user_id]])

        current_markup = callback.message.reply_markup
        skill_msg = RepliesManager.get("skill_info", skill_name=skill["name"], skill_desc=skill["description"])
        await callback.message.edit_text(text=skill_msg, parse_mode=ParseMode.HTML, reply_markup=current_markup)

    @staticmethod
    @router.callback_query(lambda c: c.data == "skill_next")
    async def skill_back(callback: CallbackQuery) -> None:
        user_id = callback.from_user.id
        user = UserManager.get_user(user_id)
        if len(user.skills) == 1:
            return
        if GameBot.skill_pages[user_id] != len(user.skills) - 1:
            GameBot.skill_pages[user_id] += 1
        else:
            GameBot.skill_pages[user_id] = 0

        skill = UserManager.get_skill(user.skills[GameBot.skill_pages[user_id]])

        current_markup = callback.message.reply_markup
        skill_msg = RepliesManager.get("skill_info", skill_name=skill["name"], skill_desc=skill["description"])
        await callback.message.edit_text(text=skill_msg, parse_mode=ParseMode.HTML, reply_markup=current_markup)

    @staticmethod
    @router.callback_query(lambda c: c.data == "inventory_back")
    async def inventory_back(callback: CallbackQuery) -> None:
        user_id = callback.from_user.id
        user = UserManager.get_user(user_id)
        if len(user.inventory) <= 10:
            return
        if GameBot.inventory_pages[user_id] != 0:
            GameBot.inventory_pages[user_id] -= 1
        else:
            GameBot.inventory_pages[user_id] = (len(user.inventory)-1)//10

        items = ""
        page = GameBot.inventory_pages[user_id] * 10
        for i in range(min(10, len(user.inventory) - page)):
            item = UserManager.get_item(user.inventory[page + i])
            items += f"\n{page + i + 1}. {item['name']}\n{item['description']}\n"

        current_markup = callback.message.reply_markup
        inventory_msg = RepliesManager.get("inventory_info", items=items)
        await callback.message.edit_text(text=inventory_msg, parse_mode=ParseMode.HTML, reply_markup=current_markup)

    @staticmethod
    @router.callback_query(lambda c: c.data == "inventory_next")
    async def inventory_next(callback: CallbackQuery) -> None:
        user_id = callback.from_user.id
        user = UserManager.get_user(user_id)
        if len(user.inventory) <= 10:
            return
        if GameBot.inventory_pages[user_id] != (len(user.inventory)-1)//10:
            GameBot.inventory_pages[user_id] += 1
        else:
            GameBot.inventory_pages[user_id] = 0

        items = ""
        page = GameBot.inventory_pages[user_id] * 10
        for i in range(min(10, len(user.inventory) - page)):
            item = UserManager.get_item(user.inventory[page + i])
            items += f"\n{page + i + 1}. {item['name']}\n{item['description']}\n"

        current_markup = callback.message.reply_markup
        inventory_msg = RepliesManager.get("inventory_info", items=items)
        await callback.message.edit_text(text=inventory_msg, parse_mode=ParseMode.HTML, reply_markup=current_markup)
    #endregion

    @staticmethod
    @dp.message(CommandStart())
    async def start(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id in UserManager.user_list():
            help_msg = RepliesManager.get("help_msg")
            sub_help = RepliesManager.get("sub_help", **{"char_name": UserManager.get_user(user_id).char_name, "help_msg": help_msg})
        else:
            sub_help = RepliesManager.get("sub_help_first")
        start_msg = RepliesManager.get("start_msg", **{"sub_help": sub_help, "gm_id": GameBot.gm_id})

        await msg.answer(start_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("help"))
    async def help(msg: Message) -> None:
        help_msg = RepliesManager.get("help_msg")
        await msg.answer(help_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("description"))
    async def description(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id in UserManager.user_list():
            join_msg = RepliesManager.get("join", **{"char_name": UserManager.get_user(user_id).char_name})
        else:
            join_msg = RepliesManager.get("join_first")
        desc_msg = RepliesManager.get("description_msg", **{"join": join_msg})

        await msg.answer(desc_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("profile"))
    async def profile(msg: Message) -> None:
        user_id = msg.from_user.id
        if not user_id in UserManager.user_list():
            error_msg = RepliesManager.get("char_not_found_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        info = UserManager.get_user(user_id)
        profile_msg = RepliesManager.get("profile_msg",
            char_name=info.char_name, join_date=info.date_joined, action_count=info.action_count,
            char_race=info.char_race, char_class=info.char_class,
            add_info=RepliesManager.get("await_gm_info") if info.status == "await" else "",
            action=int(info.action), skill_list=\
                "\n".join([f"{i+1}. {UserManager.get_skill_name(info.skills[i])}" for i in range(len(info.skills))])
                if info.skills != [] else RepliesManager.get("no_skills_info")
        )
        await msg.answer(profile_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("skill_info"))
    async def skill_info(msg: Message) -> None:
        user_id = msg.from_user.id
        if not user_id in UserManager.user_list():
            error_msg = RepliesManager.get("char_not_found_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="<-",
            callback_data="skill_back"
        ))
        builder.add(types.InlineKeyboardButton(
            text="->",
            callback_data="skill_next"
        ))
        GameBot.skill_pages[user_id] = 0
        user = UserManager.get_user(user_id)
        if not user.skills:
            skill_msg = RepliesManager.get("no_skills_info")
            await msg.answer(skill_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        skill = UserManager.get_skill(user.skills[0])
        skill_msg = RepliesManager.get("skill_info", skill_name=skill["name"], skill_desc=skill["description"])
        await msg.answer(skill_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=builder.as_markup())

    @staticmethod
    @dp.message(Command("inventory"))
    async def inventory(msg: Message) -> None:
        user_id = msg.from_user.id
        if not user_id in UserManager.user_list():
            error_msg = RepliesManager.get("char_not_found_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="<-",
            callback_data="inventory_back"
        ))
        builder.add(types.InlineKeyboardButton(
            text="->",
            callback_data="inventory_next"
        ))
        GameBot.inventory_pages[user_id] = 0
        user = UserManager.get_user(user_id)
        if not user.inventory:
            inventory_msg = RepliesManager.get("inventory_empty_info")
            await msg.answer(inventory_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        items = ""
        page = GameBot.inventory_pages[user_id]*10
        for i in range(min(10, len(user.inventory) - page)):
            item = UserManager.get_item(user.inventory[page+i])
            items += f"\n{page + i + 1}. {item['name']}\n{item['description']}\n"

        inventory_msg = RepliesManager.get("inventory_info", items=items)
        await msg.answer(inventory_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True,
                         reply_markup=builder.as_markup())

    @staticmethod
    @dp.message(Command("action"))
    async def action(msg: Message) -> None:
        user_id = msg.from_user.id
        if not user_id in UserManager.user_list():
            error_msg = RepliesManager.get("char_not_found_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        user = UserManager.get_user(user_id)
        if user.status == "await":
            error_msg = RepliesManager.get("not_approved_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return
        if not user.action:
            error_msg = RepliesManager.get("no_actions_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        GameBot.await_messages[user_id] = {"status": AwaitStatus.ACTION}
        action_msg = RepliesManager.get("action_msg")
        await msg.answer(action_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    async def get_action(msg: Message) -> None:
        user_id = msg.from_user.id
        GameBot.await_messages.pop(user_id)

        UserManager.do_action(user_id)
        send_msg = RepliesManager.get("gm_msg_send")
        await msg.answer(send_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

        name = UserManager.get_user(user_id).char_name
        gm_msg = RepliesManager.get("new_action", char_name=name, user_id=user_id, action=msg.text)
        await GameBot.get_bot().send_message(chat_id=GameBot.gm_id, text=gm_msg)

    @staticmethod
    @dp.message(Command("ask_gm"))
    async def ask_gm(msg: Message) -> None:
        user_id = msg.from_user.id
        if not user_id in UserManager.user_list():
            error_msg = RepliesManager.get("char_not_found_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        user = UserManager.get_user(user_id)
        if user.ask_ban:
            error_msg = RepliesManager.get("ask_ban_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        GameBot.await_messages[user_id] = {"status": AwaitStatus.ASK}
        ask_msg = RepliesManager.get("ask_gm_msg")
        await msg.answer(ask_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    async def get_ask(msg: Message) -> None:
        user_id = msg.from_user.id
        GameBot.await_messages.pop(user_id)

        send_msg = RepliesManager.get("gm_msg_send")
        await msg.answer(send_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

        name = UserManager.get_user(user_id).char_name
        gm_msg = RepliesManager.get("new_ask", char_name=name, user_id=user_id, ask=msg.text)
        await GameBot.get_bot().send_message(chat_id=GameBot.gm_id, text=gm_msg)

    #region Create character
    @staticmethod
    @dp.message(Command("create_character"))
    async def create_character(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id in UserManager.user_list():
            error_msg = RepliesManager.get("char_exist_error")
            await msg.answer(error_msg)
            return
        GameBot.await_messages[user_id] = {"status": AwaitStatus.INFO}

        char_msg = RepliesManager.get("create_char")
        await msg.answer(char_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    async def get_basic_info(msg: Message) -> None:
        user_id = msg.from_user.id
        info = msg.text.split("\n")
        if len(info) != 3:
            error_msg = RepliesManager.get("parse_error")
            await msg.answer(error_msg)
            return

        GameBot.await_messages[user_id] = \
        {
            "status": AwaitStatus.RACE,
            "name": info[0], "race": info[1], "class": info[2]
        }

        await_msg = RepliesManager.get("await_race")
        await msg.answer(await_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    async def get_race_desc(msg: Message) -> None:
        user_id = msg.from_user.id
        GameBot.await_messages[user_id]["status"] = AwaitStatus.CLASS
        GameBot.await_messages[user_id]["race_desc"] = msg.text

        await_msg = RepliesManager.get("await_class")
        await msg.answer(await_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    async def get_class_desc(msg: Message) -> None:
        user_id = msg.from_user.id
        GameBot.await_messages[user_id]["status"] = AwaitStatus.DESCRIPTION
        GameBot.await_messages[user_id]["class_desc"] = msg.text


        await_msg = RepliesManager.get("await_description")
        await msg.answer(await_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    async def get_char_desc(msg: Message) -> None:
        user_id = msg.from_user.id
        info = GameBot.await_messages.pop(user_id)

        now = datetime.date.today()
        UserManager.create(
            user_id=user_id, date_joined=now.strftime("%d.%m %Y"), action_count=0,
            char_name=info["name"], char_race=info["race"], char_class=info["class"],
            action=False, skills=[]
        )

        await_msg = RepliesManager.get("await_gm")
        await msg.answer(await_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

        gm_msg = RepliesManager.get("new_user",
            user_id=user_id, char_name=info["name"],
            char_race=info["race"], race_desc=info["race_desc"],
            char_class=info["class"], class_desc=info["class_desc"],
            description=msg.text
        )
        await GameBot.get_bot().send_message(chat_id=user_id, text=gm_msg)
    #endregion

    #region GM commands
    @staticmethod
    @dp.message(Command("approve"))
    async def approve(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id != GameBot.gm_id:
            return

        args = msg.text.split()
        if len(args) != 2:
            error_msg = RepliesManager.get("parse_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        UserManager.approve_user(int(args[1]))
        approve_msg = RepliesManager.get("approve_msg")
        await GameBot.get_bot().send_message(chat_id=args[1], text=approve_msg, parse_mode=ParseMode.HTML)

        gm_msg = RepliesManager.get("user_approved")
        await msg.answer(gm_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("reject"))
    async def reject(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id != GameBot.gm_id:
            return

        args = msg.text.split()
        if len(args) < 3:
            error_msg = RepliesManager.get("parse_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        UserManager.reject_user(int(args[1]))
        reject_msg = RepliesManager.get("reject_msg", reason=" ".join(args[2:]))
        await GameBot.get_bot().send_message(chat_id=args[1], text=reject_msg, parse_mode=ParseMode.HTML)

        gm_msg = RepliesManager.get("user_rejected")
        await msg.answer(gm_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("send_msg"))
    async def send_msg(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id != GameBot.gm_id:
            return

        args = msg.text.split()
        if len(args) < 3:
            error_msg = RepliesManager.get("parse_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        from_gm_msg = RepliesManager.get("from_gm", msg=" ".join(args[2:]))
        await GameBot.get_bot().send_message(chat_id=args[1], text=from_gm_msg, parse_mode=ParseMode.HTML)

        gm_msg = RepliesManager.get("msg_sent")
        await msg.answer(gm_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("reject_action"))
    async def reject_action(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id != GameBot.gm_id:
            return

        args = msg.text.split()
        print(args)
        if len(args) < 3:
            error_msg = RepliesManager.get("parse_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        UserManager.reject_action(int(args[1]))
        reject_msg = RepliesManager.get("reject_action_msg", reject=" ".join(args[2:]))
        await GameBot.get_bot().send_message(chat_id=args[1], text=reject_msg, parse_mode=ParseMode.HTML)

        gm_msg = RepliesManager.get("action_reject")
        await msg.answer(gm_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("ban_ask"))
    async def ban_ask(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id != GameBot.gm_id:
            return

        args = msg.text.split()
        if len(args) != 2:
            error_msg = RepliesManager.get("parse_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        UserManager.ban_ask(int(args[1]))
        gm_msg = RepliesManager.get("user_banned")
        await msg.answer(gm_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("unban_ask"))
    async def unban_ask(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id != GameBot.gm_id:
            return

        args = msg.text.split()
        if len(args) != 2:
            error_msg = RepliesManager.get("parse_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        UserManager.unban_ask(int(args[1]))
        gm_msg = RepliesManager.get("user_unbanned")
        await msg.answer(gm_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    @staticmethod
    @dp.message(Command("add_skill"))
    async def add_skill(msg: Message) -> None:
        user_id = msg.from_user.id
        if user_id != GameBot.gm_id:
            return

        args = msg.text.split()
        if len(args) != 3:
            error_msg = RepliesManager.get("parse_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        status = UserManager.add_skill(int(args[1]), args[2])
        if not status:
            error_msg = RepliesManager.get("skill_exist_error")
            await msg.answer(error_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        skill_msg = RepliesManager.get("new_skill_added", skill_name=UserManager.get_skill_name(args[2]))
        await GameBot.get_bot().send_message(chat_id=args[1], text=skill_msg, parse_mode=ParseMode.HTML)

        gm_msg = RepliesManager.get("skill_added")
        await msg.answer(gm_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    #endregion

    @staticmethod
    @dp.message()
    async def message(msg: Message) -> None:
        user_id = msg.from_user.id
        if not user_id in GameBot.await_messages.keys():
            return

        match GameBot.await_messages[user_id]["status"]:
            case AwaitStatus.INFO: await GameBot.get_basic_info(msg)
            case AwaitStatus.RACE: await GameBot.get_race_desc(msg)
            case AwaitStatus.CLASS: await GameBot.get_class_desc(msg)
            case AwaitStatus.DESCRIPTION: await GameBot.get_char_desc(msg)
            case AwaitStatus.ACTION: await GameBot.get_action(msg)
            case AwaitStatus.ASK: await GameBot.get_ask(msg)