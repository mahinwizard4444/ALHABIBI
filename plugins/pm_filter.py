# Kanged From @TroJanZheX
import asyncio
import re
import ast
import random

from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, DELETE_TIME, P_TTI_SHOW_OFF, IMDB, REDIRECT_TO, \
    SINGLE_BUTTON, DEL_TEXT, SPELL_CHECK_REPLY, IMDB_TEMPLATE, START_IMAGE_URL, UNAUTHORIZED_CALLBACK_TEXT, redirected_env
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
FILTER_MOD = {}

#@Client.on_message(filters.command('autofilter'))
#async def fil_mod(client, message): 
#      mode_on = ["yes", "on", "true"]
#      mode_of = ["no", "off", "false"]

#      try: 
#         args = message.text.split(None, 1)[1].lower() 
#      except: 
#         return await message.reply("**𝙸𝙽𝙲𝙾𝙼𝙿𝙻𝙴𝚃𝙴 𝙲𝙾𝙼𝙼𝙰𝙽𝙳...**")
      
#      m = await message.reply("**𝚂𝙴𝚃𝚃𝙸𝙽𝙶.../**")

#      if args in mode_on:
#          FILTER_MODE[str(message.chat.id)] = "True" 
#          await m.edit("**𝙰𝚄𝚃𝙾𝙵𝙸𝙻𝚃𝙴𝚁 𝙴𝙽𝙰𝙱𝙻𝙴𝙳**")
      
#      elif args in mode_of:
#          FILTER_MODE[str(message.chat.id)] = "False"
#          await m.edit("**𝙰𝚄𝚃𝙾𝙵𝙸𝙻𝚃𝙴𝚁 𝙳𝙸𝚂𝙰𝙱𝙻𝙴𝙳**")
#      else:
#          await m.edit("𝚄𝚂𝙴 :- /autofilter on 𝙾𝚁 /autofilter off")



@Client.on_message((filters.group | filters.private) & filters.text & ~filters.edited & filters.incoming)
async def give_filter(client, message):
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message)

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(UNAUTHORIZED_CALLBACK_TEXT, show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    pre = 'Chat' if settings['redirect_to'] == 'Chat' else 'files'

    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                        text=f"🐠 [{get_size(file.file_size)}]🐠{file.file_name}🐠", 
                        callback_data=f'{pre}_#{file.file_id}#{query.from_user.id}'
                )
            ] 
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"🐠{file.file_name}🐠",
                    callback_data=f'{pre}_#{file.file_id}#{query.from_user.id}',
                ),
                InlineKeyboardButton(
                    text=f"🐠{get_size(file.file_size)}🐠",
                    callback_data=f'{pre}_#{file.file_id}#{query.from_user.id}',
                )
            ] 
            for file in files
        ]

    btn.insert(0, 
        [
            InlineKeyboardButton(f'🔰 {search} 🔰', 'dupe')
        ]
    )
    btn.insert(1,
        [
            InlineKeyboardButton(f'🗃️ 𝐅𝐈𝐋𝐄𝐒: {len(files)}', 'dupe'),
            InlineKeyboardButton(f'📝 𝐈𝐍𝐅𝐎', 'infoss')
        ]
    )
    

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⟲𝐁𝐀𝐂𝐊⟲", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 𝐏𝐀𝐆𝐄 {round(int(offset) / 10) + 1} / {round(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"❎ {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("⟳𝐍𝐄𝐗𝐓⟳", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⟲𝐁𝐀𝐂𝐊⟲", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"❎ {round(int(offset) / 10) + 1} / {round(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("⟳𝐍𝐄𝐗𝐓⟳", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )

    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("Not For You", show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.message_id)
    if not movies:
        return await query.answer("You are clicking on an old button which is expired.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('😌താങ്കളുടെ സിനിമ ഉണ്ടോന്ന് പരിശോധിക്കുന്നു... \n\n\n waiting.... \n\n\n')
    
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            k = await query.message.edit_text(
            text="▣▢▢▢▢▢"
        )
            k = await query.message.edit_text(
            text="▣▣▢▢▢▢"
        )
            k = await query.message.edit_text(
            text="▣▣▣▢▢▢"
        )
            k = await query.message.edit_text(
            text="▣▣▣▣▢▢"
        )
            k = await query.message.edit_text(
            text="▣▣▣▣▣▢"
        )
            k = await query.message.edit_text(
            text="▣▣▣▣▣▣"
        )
            k = await query.message.edit('😄നിങ്ങളുടെ മൂവീസ് ഉടനെ ആഡ് ചെയ്യുന്നതാണ്.@nasrani_update_join @munnipopz')
        await asyncio.sleep(10000)
        


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('Piracy Is Crime')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Piracy Is Crime')

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Piracy Is Crime')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == "creator") or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == "creator") or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode="md"
        )
        return await query.answer('Piracy Is Crime')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode="md")
        return await query.answer('Piracy Is Crime')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode="md"
            )
        return await query.answer('Piracy Is Crime')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode="md"
            )
        return await query.answer('Piracy Is Crime')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('Piracy Is Crime')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id, rid = query.data.split("#")

        if int(rid) not in [query.from_user.id, 0]:
            return await query.answer(UNAUTHORIZED_CALLBACK_TEXT, show_alert=True)

        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        mention = query.from_user.mention
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)                                                      
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('Check PM, I have sent files in pm', show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    
    elif query.data.startswith("Chat"):
        ident, file_id, rid = query.data.split("#")

        if int(rid) not in [query.from_user.id, 0]:
            return await query.answer(UNAUTHORIZED_CALLBACK_TEXT, show_alert=True)

        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        mention = query.from_user.mention
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
            size = size
            mention = mention
        if f_caption is None:
            f_caption = f"{files.file_name}"
            size = f"{files.file_size}"
            mention = f"{query.from_user.mention}"

        try:
            buttons = [
                    [
                        InlineKeyboardButton('Series', url='https://t.me/NasraniSeries'),
                        InlineKeyboardButton('Movies', url='https://t.me/nasrani_update'),
                    ]
                    ]
            msg = await client.send_cached_media(
                chat_id=AUTH_CHANNEL,
                file_id=file_id,
                caption=f'<b> 𝐇𝐞𝐲 👋 {query.from_user.mention} </b>😍\n 📂 Mᴏᴠɪᴇ Nᴀᴍᴇ : <code>{title}</code>\n ⚙️ Mᴏᴠɪᴇ Sɪᴢᴇ: {size}  \n\n⚠️ കോപ്പി റൈറ്റ് ഉള്ളത് കൊണ്ട് ഈ ഒരു ഫയൽ 5 മിനിറ്റ് കൊണ്ട് ഇവിടെ നിന്നും ഡിലേറ്റാവും...!!!\n\n\nഇവിടെ നിന്നും വേറെ എവിടേലും മാറ്റിയതിന് ശേഷം ഡൗൺലോഡ് ചെയ്യുക...!!!\nFILES FORWARD TO YOUR SAVED MESSAGES\n\n\nAll files here Gets Deleted With in 5 Minutes\n╔════ ᴊᴏɪɴ ᴡɪᴛʜ ᴜs ═════╗\n\n♻️ 𝙅𝙊𝙄𝙉 :- @nasrani_update\n♻️ 𝙅𝙊𝙄𝙉 :- @NasraniSeries\n╚════ ᴊᴏɪɴ ᴡɪᴛʜ ᴜs ═════╝</b>\n',
                
                protect_content=True if ident == "filep" else False,
                reply_markup=InlineKeyboardMarkup(buttons)
                    
            )
            msg1 = await query.message.reply(
                f'<b> 𝐇𝐞𝐲 👋 {query.from_user.mention} </b>😍\n\n<b>📫 Your File is Ready</b>\n\n'           
                f'<b>📂 Mᴏᴠɪᴇ Nᴀᴍᴇ</b> : <code>{title}</code>\n\n'              
                f'<b>⚙️ Mᴏᴠɪᴇ Sɪᴢᴇ</b> : <b>{size}</b>',
                True,
                'html',
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(f'ɪɴғᴏ', 'infos')
                        ],
                        [
                            InlineKeyboardButton("⚠️ Can't Access ❓ Click Here ⚠️", url=f'https://t.me/+Md9dwytUK1NhNTc9')
                        ],                       
                        [
                            InlineKeyboardButton('📥 Download 📥 ', url = msg.link)
                        ]
                    ]
                )
            )
            await query.answer('Check Out The Chat',)
            await asyncio.sleep(300)
            await msg1.delete()
            await msg.delete()
            del msg1, msg
        except Exception as e:
            logger.exception(e, exc_info=True)
            await query.answer(f"Encountering Issues", True)

    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness, But Don't Be Oversmart 😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        mention = query.from_user.mention
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
                size = size
                mention = mention
        if f_caption is None:
            f_caption = f"{title}"
        if size is None:
            size = f"{size}"
        if mention is None:
            mention = f"{mention}"

        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )
    elif query.data == "pages":
        await query.answer()
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('🎁𝐀𝐝𝐝 𝐌𝐞 𝐓𝐨 𝐘𝐨𝐮𝐫 𝐆𝐫𝐨𝐮𝐩𝐬🎁', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🔍𝐒𝐞𝐚𝐫𝐜𝐡🔎', switch_inline_query_current_chat=''),
            InlineKeyboardButton('🎭𝐔𝐩𝐝𝐚𝐭𝐞𝐬🎭', url='https://t.me/mazhatthullikal')
            ],[
            InlineKeyboardButton('🕵️𝐇𝐞𝐥𝐩🕵️', callback_data='help'),
            InlineKeyboardButton('😊𝐀𝐛𝐨𝐮𝐭😊', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="▣▢▢▢▢▢"
        )
        await query.message.edit_text(
            text="▣▣▢▢▢▢"
        )
        await query.message.edit_text(
            text="▣▣▣▢▢▢"
        )
        await query.message.edit_text(
            text="▣▣▣▣▢▢"
        )
        await query.message.edit_text(
            text="▣▣▣▣▣▢"
        )
        await query.message.edit_text(
            text="▣▣▣▣▣▣"
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode='html'
        )
        
        
        await query.answer('Piracy Is Crime')
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('𝖥𝗂𝗅𝗍𝖾𝗋', callback_data='hud'),
            InlineKeyboardButton('𝖨𝗆𝖽𝖻', callback_data='imbd'),
            InlineKeyboardButton('𝖯𝗎𝗋𝗀𝖾', callback_data='purge'),
            InlineKeyboardButton('𝖳𝗀𝗋𝖺𝗉𝗁', callback_data='tgraph')
            ],[
            InlineKeyboardButton('𝖬𝖾𝗆𝖾', callback_data='fun'),
            InlineKeyboardButton('𝖬𝗎𝗍𝖾', callback_data='mute'),
            InlineKeyboardButton('𝖡𝖺𝗇', callback_data='ban'),
            InlineKeyboardButton('𝖢𝗈𝗇𝗇𝖾𝖼𝗍𝗂𝗈𝗇', callback_data='coct')
            ],[
            InlineKeyboardButton('𝖯𝗂𝗇', callback_data='pin'),
            InlineKeyboardButton('𝖨𝗇𝖿𝗈', callback_data='info'),
            InlineKeyboardButton('𝖩𝗌𝗈𝗇', callback_data='json'),
            InlineKeyboardButton('𝖯𝗂𝗇𝗀', callback_data='ping')
            ],[
            InlineKeyboardButton('𝖢𝗈𝗏𝗂𝖽', callback_data='covid'),
            InlineKeyboardButton('𝖲𝗈𝗇𝗀', callback_data='song'),
            InlineKeyboardButton('Carbon', callback_data='carbon'),          
            InlineKeyboardButton('𝖯𝖺𝗌𝗍𝖾', callback_data='paste')
            ],[
            InlineKeyboardButton('𝖦-𝖳𝗋𝖺𝗇𝗌', callback_data='gtrans'),
            InlineKeyboardButton('TTS', callback_data='tts'),
            InlineKeyboardButton('𝖲𝗍𝖺𝗍𝗌', callback_data='stats'),
            InlineKeyboardButton('Logo', callback_data='lego')   
            ],[
            InlineKeyboardButton('Torrent', callback_data='trnt'),
            InlineKeyboardButton('Url short', callback_data='urlshrt'),
            InlineKeyboardButton('Weather', callback_data='weather'),
            InlineKeyboardButton('Country', callback_data='cntry')
            ],[     
            InlineKeyboardButton('𝖢𝗅𝗈𝗌𝖾', callback_data='close_data'),
            InlineKeyboardButton('Home', callback_data='start'),
            InlineKeyboardButton('𝖡𝖺𝖼𝗄', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text="▣▢▢▢▢▢"
        )
        await query.message.edit_text(
            text="▣▣▢▢▢▢"
        )
        await query.message.edit_text(
            text="▣▣▣▢▢▢"
        )
        await query.message.edit_text(
            text="▣▣▣▣▢▢"
        )
        await query.message.edit_text(
            text="▣▣▣▣▣▢"
        )
        await query.message.edit_text(
            text="▣▣▣▣▣▣"
        )
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )

    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('ᴍᴀɴᴜᴇʟ ғɪʟᴛᴇʀ', callback_data='manuelfilter'),
            InlineKeyboardButton('ᴀᴜᴛᴏ ғɪʟᴛᴇʀ', callback_data='autofilter'),
            InlineKeyboardButton('ᴄᴏɴɴᴇᴄᴛɪᴏɴs', callback_data='coct'),
            ],[
            InlineKeyboardButton('sᴏɴɢ', callback_data='songs'),
            InlineKeyboardButton('ᴇxᴛʀᴀ', callback_data='extra'),
            InlineKeyboardButton("ᴠɪᴅᴇᴏ", callback_data='video'),
            ],[
            InlineKeyboardButton('ᴘɪɴ', callback_data='pin'), 
            InlineKeyboardButton('ᴘᴀsᴛᴇ', callback_data='pastes'),
            InlineKeyboardButton("ɪᴍᴀɢᴇ", callback_data='image'),
            ],[
            InlineKeyboardButton('ғᴜɴ', callback_data='fun'), 
            InlineKeyboardButton('ᴊsᴏɴ', callback_data='son'),
            InlineKeyboardButton('ᴛᴛs', callback_data='ttss'),
            ],[
            InlineKeyboardButton('ᴘᴜʀɢᴇ', callback_data='purges'),
            InlineKeyboardButton('ᴘɪɴɢ', callback_data='pings'),
            InlineKeyboardButton('ᴛᴇʟᴇɢʀᴀᴘʜ', callback_data='tele'),
            ],[
            InlineKeyboardButton('ᴡʜᴏɪs', callback_data='whois'),
            InlineKeyboardButton('ᴍᴜᴛᴇ', callback_data='restric'),
            InlineKeyboardButton('ᴋɪᴄᴋ', callback_data='zombies'),
            ],[
            InlineKeyboardButton('ʀᴇᴘᴏʀᴛ', callback_data='report'),
            InlineKeyboardButton('ʏᴛ-ᴛʜᴜᴍʙ', callback_data='ytthumb'),
            InlineKeyboardButton('sᴛɪᴄᴋᴇʀ-ɪᴅ', callback_data='sticker'),
            ],[
            InlineKeyboardButton('ᴄᴏᴠɪᴅ', callback_data='corona'),
            InlineKeyboardButton('ᴀᴜᴅɪᴏ-ʙᴏᴏᴋ', callback_data='abook'),
            InlineKeyboardButton('ᴜʀʟ-sʜᴏʀᴛ', callback_data='urlshort'),
            ],[
            InlineKeyboardButton('ɢ-ᴛʀᴀɴs', callback_data='gtrans'),
            InlineKeyboardButton('ғɪʟᴇ-sᴛᴏʀᴇ', callback_data='newdata'),
            InlineKeyboardButton('sʜᴀʀᴇ-ᴛᴇxᴛ', callback_data='sharetext'),
            ],[
            InlineKeyboardButton('ᴘᴀssᴡᴏʀᴅ-ɢᴇɴ', callback_data='genpassword'),
            InlineKeyboardButton('ᴀᴘᴘʀᴏᴠᴇ', callback_data='approve'),
            InlineKeyboardButton('ɢʀᴇᴇᴛɪɴɢs', callback_data='welcome'),
            ],[
            InlineKeyboardButton('ʟᴏᴄᴋs', callback_data='lock'),
            InlineKeyboardButton('ɴᴏᴛᴇs', callback_data='note'),
            InlineKeyboardButton('ᴘᴜʀɢᴇ', callback_data='purge'),
            ],[
            InlineKeyboardButton('ʀᴜʟᴇs', callback_data='rule'),
            InlineKeyboardButton('ᴜʀʟ-sʜᴏʀᴛɴᴇʀ', callback_data='url'),
            InlineKeyboardButton('ᴛᴏʀʀᴇɴᴛ', callback_data='torrent'),
            ],[
            InlineKeyboardButton('ᴡᴀʀɴ', callback_data='warn'),
            InlineKeyboardButton('ᴍᴀʟʟᴜ ᴀᴜɴᴛʏ', callback_data='aunty'),
            InlineKeyboardButton('ᴍᴀᴍᴍᴏᴋᴀ', callback_data='mammoka'),
            ],[
            InlineKeyboardButton('Bot Status', callback_data='restatus'),
            InlineKeyboardButton('Text To Img', callback_data='img'),
            InlineKeyboardButton('ՏTYᒪIՏᕼ ᖴOᑎTՏ', callback_data='fonts'),
            ],[
            InlineKeyboardButton('Carbon', callback_data='carbon'),
            InlineKeyboardButton('Lyrics', callback_data='lyrics'),
            InlineKeyboardButton('IP Address', callback_data='ip'),
            ],[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='start'),
            InlineKeyboardButton('sᴛᴀᴛᴜs', callback_data='stats'),
            InlineKeyboardButton('ᴄʟᴏsᴇ x', callback_data='close_data')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "hellp":
        buttons = [[
            InlineKeyboardButton('𝑀𝑎𝑛𝑢𝑒𝑙 𝐹𝑖𝑙𝑡𝑒𝑟', callback_data='manuelfilter'),
            InlineKeyboardButton('𝐴𝑢𝑡𝑜 𝐹𝑖𝑙𝑡𝑒𝑟', callback_data='autofilter'),
            InlineKeyboardButton('𝐶𝑜𝑛𝑛𝑒𝑐𝑡𝑖𝑜𝑛𝑠', callback_data='coct')
            ],[
            InlineKeyboardButton('𝑆𝑜𝑛𝑔', callback_data='songs'),
            InlineKeyboardButton('𝐸𝑥𝑡𝑟𝑎', callback_data='extra'),
            InlineKeyboardButton("𝑉𝑖𝑑𝑒𝑜", callback_data='video')
            ],[
            InlineKeyboardButton('𝑃𝑖𝑛', callback_data='pin'), 
            InlineKeyboardButton('𝑃𝑎𝑠𝑡𝑒', callback_data='pastes'),
            InlineKeyboardButton("𝐼𝑚𝑎𝑔𝑒", callback_data='image')
            ],[
            InlineKeyboardButton('𝐹𝑢𝑛', callback_data='fun'), 
            InlineKeyboardButton('𝐽𝑠𝑜𝑛', callback_data='son'),
            InlineKeyboardButton('𝑇𝑇𝑆', callback_data='ttss')
            ],[
            InlineKeyboardButton('𝑃𝑢𝑟𝑔𝑒', callback_data='purges'),
            InlineKeyboardButton('𝑃𝑖𝑛𝑔', callback_data='pings'),
            InlineKeyboardButton('𝑇𝑒𝑙𝑒𝑔𝑟𝑎𝑝𝒉', callback_data='tele')
            ],[
            InlineKeyboardButton('𝑊𝒉𝑜𝑖𝑠', callback_data='whois'),
            InlineKeyboardButton('𝑀𝑢𝑡𝑒', callback_data='restric'),
            InlineKeyboardButton('𝐾𝑖𝑐𝑘', callback_data='zombies')
            ],[
            InlineKeyboardButton('𝑅𝑒𝑝𝑜𝑟𝑡', callback_data='report'),
            InlineKeyboardButton('𝑌𝑡-𝑇𝒉𝑢𝑚𝑏', callback_data='ytthumb'),
            InlineKeyboardButton('𝑆𝑡𝑖𝑐𝑘𝑒𝑟-𝐼𝑑', callback_data='sticker')
            ],[
            InlineKeyboardButton('𝐶𝑜𝑣𝑖𝑑', callback_data='corona'),
            InlineKeyboardButton('𝐴𝑢𝑑𝑖𝑜-𝐵𝑜𝑜𝑘', callback_data='abook'),
            InlineKeyboardButton('𝑈𝑟𝑙-𝑆𝒉𝑜𝑟𝑡', callback_data='urlshort')
            ],[
            InlineKeyboardButton('𝐺-𝑇𝑟𝑎𝑛𝑠', callback_data='gtrans'),
            InlineKeyboardButton('𝐹𝑖𝑙𝑒-𝑆𝑡𝑜𝑟𝑒', callback_data='newdata'),
            ],[
            InlineKeyboardButton('𝐵𝑎𝑐𝑘', callback_data='start'),
            InlineKeyboardButton('𝑆𝑡𝑎𝑡𝑢𝑠', callback_data='stats'),
            InlineKeyboardButton('𝐶𝑙𝑜𝑠𝑒 ✗', callback_data='close_data')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.answer("𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝗍𝗈 𝗆𝗒 𝖧𝖾𝗅𝗉 𝗆𝗈𝖽𝗎𝗅𝖾")
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "about":
        buttons= [[
            InlineKeyboardButton('ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀᴛ', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('ғɪʟᴇ sᴛᴀᴛᴜs', callback_data='stats'),
            InlineKeyboardButton('sᴏᴜʀᴄᴇ', callback_data='source')
            ],[
            InlineKeyboardButton('🔍sᴇᴀʀᴄʜ ᴍᴏᴠɪᴇ🔎', switch_inline_query_current_chat='')
            ],[
            InlineKeyboardButton('🍿ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ ɢʀᴏᴜᴘ🍿', url='https://t.me/MovieHubOfficialGroup')
            ],[
            InlineKeyboardButton('ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs', callback_data='help')
            ],[
            InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data='start'),
            InlineKeyboardButton('ᴄʟᴏsᴇ ✗', callback_data='close_data'),
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "ip":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.IP_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "lyrics":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.LYRICS_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "carbon":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CARBON_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "fonts":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FONTS_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "img":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.IMG_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "restatus":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BOTSTATUS_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "mammoka":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MAMMOKA_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "aunty":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUNTY_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "warn":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.WARN_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "url":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.URL_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "url":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.URL_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "torrent":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.TORRENT_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "rule":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.RULES_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "purge":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.PURGE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "note":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.NOTE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "approve":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.APPROVE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "lock":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.LOCK_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "welcome":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.WELCOME_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "genpassword":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GEN_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "sharetext":
        buttons = [[
            InlineKeyboardButton('« 𝐵𝑎𝑐𝑘', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SHARE_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "restric":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.RESTRIC_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "image":
        buttons= [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.IMAGE_TXT.format(temp.B_NAME),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "whois":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.WHOIS_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "corona":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CORONA_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "urlshort":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.URLSHORT_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "zombies":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ZOMBIES_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "fun":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FUN_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "video":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='song')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.VIDEO_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "pin":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.PIN_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "son":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.JSON_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "pastes":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.PASTE_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "pings":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.PINGS_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "ttss":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GTRANS_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "purges":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.PURGE_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "tele":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.TELE_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )         
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='about')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help'),
            InlineKeyboardButton('𝙱𝚄𝚃𝚃𝙾𝙽𝚂', callback_data='button')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='manuelfilter')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help'),
            InlineKeyboardButton('𝙰𝙳𝙼𝙸𝙽', callback_data='admin')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "gtrans":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help'),
            InlineKeyboardButton('𝙻𝙰𝙽𝙶 𝙲𝙾𝙳𝙴𝚂', url='https://cloud.google.com/translate/docs/languages')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GTRANS_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "report":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.REPORT_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "sticker":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.STICKER_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "ytthumb":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.YTTHUMB_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='extra')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "abook":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOOK_TXT,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "newdata":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FILE_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "songs":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SONG_TXT,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help'),
            InlineKeyboardButton('𝚁𝙴𝙵𝚁𝙴𝚂𝙷', callback_data='rfrsh')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "rfrsh":
        await query.answer("𝐿𝑒𝑡 𝑀𝑒 𝑆𝑒𝑒 𝑇𝒉𝑒 𝑀𝑜𝑛𝑔𝑜 𝐷𝐵")
        buttons = [[
            InlineKeyboardButton('𝙱𝙰𝙲𝙺', callback_data='help'),
            InlineKeyboardButton('𝚁𝙴𝙵𝚁𝙴𝚂𝙷', callback_data='rfrsh')
        ]]
        reply1 = await query.message.reply_text(
            text="▢▢▢"
        )
        await asyncio.sleep(0.5)
        reply2 = await reply1.edit_text(
            text="▣▢▢"
        )
        await asyncio.sleep(0.5)
        reply3 = await reply2.edit_text(
            text="▣▣▢"
        )
        await asyncio.sleep(0.5)
        reply4 = await reply3.edit_text(
            text="▣▣▣"
        )
        await reply4.delete()
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode='html'
      )
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return 

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('𝐅𝐈𝐋𝐓𝐄𝐑 𝐁𝐔𝐓𝐓𝐎𝐍',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('𝐒𝐈𝐍𝐆𝐋𝐄' if settings["button"] else '𝐃𝐎𝐔𝐁𝐋𝐄',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐁𝐎𝐓 𝐏𝐌', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["botpm"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐅𝐈𝐋𝐄 𝐒𝐄𝐂𝐔𝐑𝐄',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["file_secure"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐈𝐌𝐃𝐁', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["imdb"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐒𝐏𝐄𝐋𝐋 𝐂𝐇𝐄𝐂𝐊',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["spell_check"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('𝐖𝐄𝐋𝐂𝐎𝐌𝐄', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ 𝐘𝐄𝐒' if settings["welcome"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)

   
    elif query.data == "close":
        await query.message.delete()
    elif query.data == 'tips':
        await query.answer("=> Ask with correct spelling\n=> Don't ask movies those are not released in OTT Some Of Theatre Quality Available🤧\n=> For better results:\n\t\t\t\t\t\t- MovieName year\n\t\t\t\t\t\t- Eg: Kuruthi 2021", True)
    elif query.data == 'infos':
        await query.answer("⚠︎ Information ⚠︎\n\nAfter 3 minutes this message will be automatically deleted\n\nIf you do not see the requested movie / series file, look at the next page\n\nⒸᴍᴏᴠɪᴇs ɢʀᴏᴜᴘ", True)
    elif query.data == 'infoss':
        await query.answer("Automatic deleting 5 minut. Forwerd file your save storage😌", True)
    elif query.data == 'imdb':
        await query.answer("{search}", True)
    
    elif query.data == 'series':
        await query.answer("sᴇʀɪᴇs ʀᴇǫᴜᴇsᴛ ғᴏʀᴍᴀᴛ\n\nɢᴏ ᴛᴏ ɢᴏᴏɢʟᴇ ➠ ᴛʏᴘᴇ sᴇʀɪᴇs ɴᴀᴍᴇ ➠ ᴄᴏᴘʏ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ➠ ᴘᴀsᴛᴇ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ\n\nᴇxᴀᴍᴘʟᴇ : Alive ᴏʀ Alive S01E01\n\n🚯 ᴅᴏɴᴛ ᴜsᴇ ➠ ':(!,./)\n\nⒸᴍᴏᴠɪᴇs ɢʀᴏᴜᴘ", True)

    try: await query.answer('Piracy Is Crime') 
    except: pass


async def auto_filter(client, msg: pyrogram.types.Message, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    
    pre = 'filep' if settings['file_secure'] else 'file'
    pre = 'Chat' if settings['redirect_to'] == 'Chat' else pre

    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"🐠{file.file_name}🐠",
                    callback_data=f'{pre}#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}',
                ),
                InlineKeyboardButton(
                    text=f"🐠{get_size(file.file_size)}🐠",
                    callback_data=f'{pre}_#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}',
                )
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                        text=f"🐠 [{get_size(file.file_size)}]🐠{file.file_name}🐠", 
                        callback_data=f'{pre}#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}'
                )
            ] 
            for file in files
        ]

    
    btn.insert(0,
        [
            InlineKeyboardButton(f'🔰 {search} 🔰', 'infoss'),
            
        ]
    )
    btn.insert(1,
        [
            InlineKeyboardButton(f'📁 Files: {total_results}', 'dupe'),
            InlineKeyboardButton(f"🎭 {search} 🎭",callback_data="pages")
        ]
    )
    btn.insert(14,
        [
            InlineKeyboardButton(f"🐟{message.chat.title}🐟",url="https://t.me/nasrani_update"),
            InlineKeyboardButton(f"🦄{message.from_user.id}🦄",url="tg://openmessage?user_id={user_id}")
        ]
    )
  

    await message.reply_chat_action("Typing")
    m=await message.reply_sticker("CAACAgUAAx0CQTCW0gABB5EUYkx6-OZS7qCQC6kNGMagdQOqozoAAgQAA8EkMTGJ5R1uC7PIECME") 
    await asyncio.sleep(2)
    await m.delete()
    

    if offset != "":
        key = f"{message.chat.id}-{message.message_id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"❎ 1/{round(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="⟳𝐍𝐄𝐗𝐓⟳", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="❎ 1/1", callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            mention_bot=temp.MENTION,
            mention_user=message.from_user.mention if message.from_user else message.sender_chat.title,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"👮‍♂ ɴᴏᴛɪᴄᴇ :ɪ𝙵 ʏᴏᴜ ᴅᴏ ɴᴏᴛ sᴇᴇ ᴛʜᴇ 𝙵ɪʟᴇ𝚂 ᴏ𝙵 ᴛʜɪ𝚂 ᴍᴏᴠɪᴇ ʏᴏᴜ ᴀ𝚂ᴋᴇᴅ 𝙵ᴏʀ. ʟᴏᴏᴋ ᴀᴛ ɴᴇ𝚇ᴛ ᴘᴀɢᴇ🔎\n©️քօաɛʀɛɖ ɮʏ :{message.chat.title}"
    if imdb and imdb.get('poster'):
        try:
            fmsg = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            fmsg = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    else:
        fmsg = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
    
    await asyncio.sleep(10)
    await fmsg.delete()
    await message.reply_text(
    text=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️",
    parse_mode="html",
    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('🎁𝐆𝐫𝐨𝐮𝐩🎁', url="http://t.me/nasrani_update")
                            ],
                                                        
                        ]
                    )
                )

    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(msg):
    query = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e)?(l)*(o)*|mal(ayalam)?|tamil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle)", "", msg.text, flags=re.IGNORECASE) # plis contribute some common words 
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply("നിങ്ങൾ ചോദിക്കുന്ന മൂവി ഇതിലുണ്ടോന്ന് ഉറപ്പ് വരുത്തുക.")
        await asyncio.sleep(8)
        await k.delete()
        return
        await asyncio.sleep(8)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE) # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)', '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*", re.IGNORECASE) # match something like Watch Niram | Amazon Prime 
        for mv in g_s:
            match  = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed)) # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True) # searching each keyword in imdb
            if imdb_s:
                movielist +=[movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist)) # removing duplicates
    if not movielist:
          
        k = await msg.reply_video(
        video= "https://telegra.ph/file/ec5404d035924f1113d8d.mp4",
        caption=f"<b>📍Hello:-നിങ്ങൾ ചോദിച്ച മൂവി വേണമെങ്കിൽ മുകളിലെ വീഡിയോ കണ്ട് അത് പോലെ സ്പെല്ലിങ് തെറ്റാതെ അയക്കുക.😌</b>",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('🎁𝐀𝐝𝐝 𝐌𝐞 𝐓𝐨 𝐘𝐨𝐮𝐫 𝐆𝐫𝐨𝐮𝐩𝐬🎁', url="http://t.me/nasrani_bot?startgroup=true")
                            ],
                            [
                                InlineKeyboardButton('🧩𝐆𝐨𝐨𝐠𝐥𝐞🧩', url="https://google.com"),
                                InlineKeyboardButton('☘𝐈𝐦𝐝𝐛☘', url="https://imdb.com")
                            ]                            
                        ]
                    )
                )         
        

                            

        await asyncio.sleep(60)
        await k.delete()
        return
    SPELL_CHECK[msg.message_id] = movielist
    btn = [[
                InlineKeyboardButton(
                    text=movie.strip(),
                    callback_data=f"spolling#{user}#{k}",
                )
            ] for k, movie in enumerate(movielist)]    
    
    btn.append(
            [
                InlineKeyboardButton("🔐𝐂𝐥𝐨𝐬𝐞🔐", callback_data=f'spolling#{user}#close_spellcheck'),
                InlineKeyboardButton("song", url="https://imdb.com")       
            ],
        )
    btn.insert(0,
            [
                InlineKeyboardButton(f'ɪɴғᴏ', 'infos'),
                InlineKeyboardButton(f'ᴍᴏᴠɪᴇ', 'movies'),
                InlineKeyboardButton(f'sᴇʀɪᴇs', 'series')
            ]
    )
   
    k = await msg.reply_sticker(
        sticker= "CAACAgUAAxkBAAJXA2GiaMWYAAEvGr39FQLCuU_qW4rH1AACHwADhq-BGkoDm80BdFrWIgQ",
        reply_markup=InlineKeyboardMarkup(btn))
    await asyncio.sleep(60)
    await k.delete()
    return k
async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                            
                            
                    elif btn == "[]":
                            await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                       
                        
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        
                         
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
