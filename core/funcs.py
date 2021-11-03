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
 