"""
Music Player, Telegram Voice Chat Bot
Copyright (c) 2021  Twist Bots <https://github.com/TwistBots>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

from config import config
from core.queue import Queue
from pyrogram.types import Message
from typing import Any, Dict, Union
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.phone import EditGroupCallTitle


GROUPS: Dict[int, Dict[str, Any]] = {}


def all_groups():
    return GROUPS.keys()


def set_default(chat_id: int) -> None:
    global GROUPS
    GROUPS[chat_id] = {}
    GROUPS[chat_id]["is_playing"] = False
    GROUPS[chat_id]["now_playing"] = None
   