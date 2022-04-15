import os
from pyrogram import Client, filters


Bot = Client(
     os.environ.get("SESSION_NAME", "No-Forward-Messages"),
     bot_token = os.environ["BOT_TOKEN"],
     api_id = int(os.environ["API_ID"]),
     api_hash = os.environ["API_HASH"]
)


@Client.on_message(filters.forwarded)
async def forward(bot, message):
	await message.delete()
