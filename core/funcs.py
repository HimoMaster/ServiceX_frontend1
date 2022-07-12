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

import os
import re
import sys
import time
import random
import aiohttp
import asyncio
import aiofiles
from config import config
from core.song import Song
from pyrogram import Client
from pytube import Playlist
from yt_dlp import YoutubeDL
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont
from pytgcalls import PyTgCalls, StreamType
from core.groups import get_group, set_title
from youtubesearchpython import VideosSearch
from typing import Tuple, Union, Optional, AsyncIterator
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    LowQualityAudio, LowQualityVideo, HighQualityAudio, HighQualityVideo,
    MediumQualityAudio, MediumQualityVideo)


safone = {}
ydl_opts = {
    "quiet": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
}
ydl = YoutubeDL(ydl_opts)
app = Client(config.SESSION, api_id=config.API_ID, api_hash=config.API_HASH)
pytgcalls = PyTgCalls(app)


themes = [
    "blue",
    "black",
    "red",
    "green",
    "grey",
    "orange",
    "pink",
    "yellow",
]


def restart():
    os.system("git pull")
    time.sleep(5)
    os.execl(sys.executable, sys.executable, *sys.argv)


def search(message: Message) -> Optional[Song]:
    query = ""
    if message.reply_to_message:
        if message.reply_to_message.audio:
            query = message.reply_to_message.audio.title
        elif message.reply_to_message.video:
            query = message.reply_to_message.video.file_name
        elif message.reply_to_message.document:
            query = message.reply_to_message.document.file_name
        else:
            query = message.reply_to_message.text
    else:
        query = extract_args(message.text)
    if query == "":
        return None
    is_yt_url, url = check_yt_url(query)
    if is_yt_url:
        return Song(url, message)
    group = get_group(message.chat.id)
    vs = VideosSearch(
        query, limit=1, language=group["lang"], region=group["lang"]
    ).result()
    if len(vs["result"]) > 0 and vs["result"][0]["type"] == "video":
        video = vs["result"][0]
        return Song(video["link"], message)
    return None


def check_yt_url(text: str) -> Tuple[bool, Optional[str]]:
    pattern = re.compile(
        "^((?:https?:)?\\/\\/)?((?:www|m)\\.)?((?:youtube\\.com|youtu.be))(\\/(?:[\\w\\-]+\\?v=|embed\\/|v\\/)?)([\\w\\-]+)([a-zA-Z0-9-_]+)?$"
    )
    matches = re.findall(pattern, text)
    if len(matches) <= 0:
        return False, None

    match = "".join(list(matches[0]))
    return True, match


def extract_args(text: str) -> str:
    if " " not in text:
        return ""
    else:
        return text.split(" ", 1)[1]


def get_quality(song: Song) -> Union[AudioPiped, AudioVideoPiped]:
    group = get_group(song.request_msg.chat.id)
    if group["is_video"]:
        if config.QUALITY.lower() == "high":
            return AudioVideoPiped(
                song.remote_url, HighQualityAudio(), HighQualityVideo(), song.headers
            )
        elif config.QUALITY.lower() == "medium":
            return AudioVideoPiped(
                song.remote_url,
                MediumQualityAudio(),
                MediumQualityVideo(),
                song.headers,
            )
        elif config.QUALITY.lower() == "low":
            return AudioVideoPiped(
                song.remote_url, LowQualityAudio(), LowQualityVideo(), song.headers
            )
        else:
            print("Invalid Quality Specified. Defaulting to High!")
            return AudioVideoPiped(
                song.remote_url, HighQualityAudio(), HighQualityVideo(), song.headers
            )
    else:
        if config.QUALITY.lower() == "high":
            return AudioPiped(song.remote_url, HighQualityAudio(), song.headers)
        elif config.QUALITY.lower() == "medium":
            return AudioPiped(song.remote_url, MediumQualityAudio(), song.headers)
        elif config.QUALITY.lower() == "low":
            return AudioPiped(song.remote_url, LowQualityAudio(), song.headers)
        else:
            print("Invalid Quality Specified. Defaulting to High!")
            return AudioPiped(song.remote_url, HighQualityAudio(), song.headers)


async def delete_messages(messages):
    await asyncio.sleep(10)
    for msg in messages:
        if msg.chat.type == "supergroup":
            try:
                await msg.delete()
            except BaseException:
                pass


async def skip_stream(song: Song, lang):
    chat = song.request_msg.chat
    if safone.get(chat.id) is not None:
        try:
            await safone[chat.id].delete()
        except BaseException:
            pass
    infomsg = await song.request_msg.reply_text(lang["downloading"])
    await pytgcalls.change_stream(
        chat.id,
        get_quality(song),
    )
    await set_title(chat.id, song.title, client=app)
    thumb = await generate_cover(
        song.title,
        chat.title,
        chat.id,
        song.thumb,
    )
    safone[chat.id] = await song.request_msg.reply_photo(
        photo=thumb,
        caption=lang["playing"]
        % (
            song.title,
            song.yt_url,
            song.duration,
            song.request_msg.chat.id,
            song.requested_by.mention
            if song.requested_by
            else song.request_msg.sender_chat.title,
        ),
        quote=False,
    )
    await infomsg.delete()
    if os.path.exists(thumb):
        os.remove(thumb)


async def start_stream(song: Song, lang):
    chat = song.request_msg.chat
    if safone.get(chat.id) is not None:
        try:
            await safone[chat.id].delete()
        except BaseException:
            pass
    infomsg = await song.request_msg.reply_text(lang["downloading"])
    await pytgcalls.join_group_call(
        chat.id,
        get_quality(song),
        stream_type=StreamType().pulse_stream,
    )
    await set_title(chat.id, song.title, client=app)
    thumb = await generate_cover(
        song.title,
        chat.title,
        chat.id,
        song.thumb,
    )
    safone[chat.id] = await song.request_msg.reply_photo(
        photo=thumb,
        caption=lang["playing"]
        % (
            song.title,
            song.yt_url,
            song.duration,
            song.request_msg.chat.id,
            song.requested_by.mention
            if song.requested_by
            else song.request_msg.sender_chat.title,
        ),
        quote=False,
    )
    await infomsg.delete()
    if os.path.exists(thumb):
        os.remove(thumb)


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(title, ctitle, chatid, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open(f"thumb{chatid}.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    theme = random.choice(themes)
    ctitle = await special_to_normal(ctitle)
    image1 = Image.open(f"thumb{chatid}.png")
    image2 = Image.open(f"theme/{theme}.PNG")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save(f"temp{chatid}.png")
    img 