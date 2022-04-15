import os 
import pyrogram
from pyrogram import Client, filters


import os
from pyrogram import Client, filters

from C import Config



@Client.on_message(filters.forwarded)
async def forward(bot, message):
	await message.delete()


@Client.on_message(filters.regex("http") | filters.regex("www") | filters.regex("@") | filters.regex("t.me"))
async def nolink(bot,message):
	try:
		await message.delete()
	except:
		return
