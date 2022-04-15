import os
from pyrogram import Client, filters





@Client.on_message(filters.forwarded)
async def forward(bot, message):
	await message.delete()
