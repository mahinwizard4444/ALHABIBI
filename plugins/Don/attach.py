# Author: Fayas (https://github.com/FayasNoushad) (@FayasNoushad)

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton



MODULES = {
    "attach": {
        "text": "Attach",
        "help_text": "**Attach**\n\n- Just send a html or markdown message\n\n- Reply /attach with link for attaching",
        "help_buttons": []
    }
}


@Client.on_message(filters.command(["attach"]) & filters.reply, group=1)
async def attach(update: Message):
    if len(update.text.split()) <= 1:
        await update.reply_text("Send command with link for attaching")
        return
    link = update.text.split(" ", 1)[1]
    await update.reply_text(
        text=f"[\u2063]({link}){update.reply_to_message.text}",
        reply_markup=update.reply_to_message.reply_markup
    )


@Client.on_message(filters.command(["modules"]), group=1)
async def modules_help(update: Message, cb=False):
    text = "**Modules**"
    buttons = []
    for module in MODULES:
        button = InlineKeyboardButton(
            text=MODULES[module]["text"],
            callback_data="module+"+module
        )
        if len(buttons) == 0 or len(buttons[-1]) >= 2:
            buttons.append([button])
        else:
            buttons[-1].append(button)
    reply_markup = InlineKeyboardMarkup(buttons)
    if cb:
        await update.message.edit_text(
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    else:
        await update.reply_text(
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )


@Client.on_message(filters.command(["module"]), group=1)
async def module_help(update: Message):
    try:
        module = update.text.split(" ", 1)[1].lower()
        await update.reply_text(
            text=MODULES[module]["help_text"],
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="🔙 Back", callback_data="modules")]]
            ),
            quote=True
        )
    except Exception as error:
        await update.reply_text(
            text=error,
            disable_web_page_preview=True,
            quote=True
        )

async def modules_cb(update):
    module = update.data.split("+")[1]
    await update.message.edit_text(
        text=MODULES[module]["help_text"],
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="🔙 Back", callback_data="modules")]]
        )
    )



@Client.on_message(filters.text & filters.private & filters.reply & filters.regex(r'https?://[^\s]+'))
async def attach(bot, update):
    await update.reply_text(
        text=f"[\u2063]({update.text}){update.reply_to_message.text}",
        reply_markup=update.reply_to_message.reply_markup
    )
