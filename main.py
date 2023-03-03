
"""
Music Player, Telegram Voice Chat Bot
Copyright (c) 2021  Twist bots <https://github.com/TwistBots>

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

import os
import json
from config import config
from core.song import Song
from pyrogram import filters
from threading import Thread
from pyrogram.types import Message
from pytgcalls.types import Update
from pyrogram.raw.types import InputPeerChannel
from pyrogram.raw.functions.phone import CreateGroupCall
from pytgcalls.exceptions import GroupCallNotFound, NoActiveGroupCall
from pytgcalls.types.stream import StreamAudioEnded, StreamVideoEnded
from core.decorators import language, register, only_admins, handle_error
from core import (
    app, ydl, safone, search, restart, get_group, get_queue, pytgcalls,
    set_group, set_title, all_groups, clear_queue, skip_stream, check_yt_url,
    extract_args, start_stream, shuffle_queue, delete_messages,
    get_youtube_playlist)


REPO = """
🤖 **Music Player**
- Repo: [GitHub](https://github.com/TwistBots/MusicPlayer)
- License: AGPL-3.0-or-later
"""


@app.on_message(
    filters.command("repo", config.PREFIXES) & ~filters.private & ~filters.edited
)
@handle_error
async def repo(_, message: Message):
    await message.reply_text(REPO, disable_web_page_preview=True)


@app.on_message(
    filters.command("ping", config.PREFIXES) & ~filters.private & ~filters.edited
)
@handle_error
async def ping(_, message: Message):
    await message.reply_text(f"¤ **Pong!**\n`{await pytgcalls.ping} ms`")


@app.on_message(
    filters.command(["start", "help"], config.PREFIXES)
    & ~filters.private
    & ~filters.edited
)
@language
@only_admins
@handle_error
async def help(_, message: Message, lang):
    await message.reply_text(lang["helpText"].replace("<prefix>", config.PREFIXES[0]))


@app.on_message(
    filters.command(["p", "play"], config.PREFIXES) & ~filters.private & ~filters.edited
)
@register
@language
@handle_error
async def play_stream(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    song = search(message)
    if song is None:
        k = await message.reply_text(lang["notFound"])
        return await delete_messages([message, k])
    ok, status = await song.parse()
    if not ok:
        raise Exception(status)
    if not group["is_playing"]:
        set_group(chat_id, is_playing=True, now_playing=song)
        try:
            await start_stream(song, lang)
        except (NoActiveGroupCall, GroupCallNotFound):
            peer = await app.resolve_peer(chat_id)
            await app.send(
                CreateGroupCall(
                    peer=InputPeerChannel(
                        channel_id=peer.channel_id,
                        access_hash=peer.access_hash,
                    ),
                    random_id=app.rnd_id() // 9000000000,
                )
            )
            await start_stream(song, lang)
        await delete_messages([message])
    else:
        queue = get_queue(chat_id)
        await queue.put(song)
        k = await message.reply_text(
            lang["addedToQueue"] % (song.title, song.yt_url, len(queue)),
            disable_web_page_preview=True,
        )
        await delete_messages([message, k])