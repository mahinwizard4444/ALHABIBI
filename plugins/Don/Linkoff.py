import os 
import pyrogram
from pyrogram import Client, filters
import os
from pyrogram import Client, filters

from C import Config

from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR



API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
BOT_TOKEN = os.environ.get('BOT_TOKEN')





@Client.on_message(filters.forwarded)
async def forward(bot, message):
	await message.delete()


@Client.on_message(filters.regex("http") | filters.regex("www") | filters.regex("@") | filters.regex("t.me"))
async def nolink(bot,message):
	try:
		await message.delete()
	except:
		return
