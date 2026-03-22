import asyncio
import logging

from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from Code_X_Mania.bot import StreamBot
from Code_X_Mania.utils.database import Database
from Code_X_Mania.utils.human_readable import humanbytes
from Code_X_Mania.vars import Var

log = logging.getLogger(__name__)
db  = Database(Var.DATABASE_URL, Var.SESSION_NAME)


async def _ensure_user(client: Client, user_id: int, first_name: str):
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id)
        try:
            await client.send_message(
                Var.BIN_CHANNEL,
                f"**New User:** [{first_name}](tg://user?id={user_id})",
            )
        except Exception:
            pass


async def _check_subscription(client: Client, chat_id: int) -> bool:
    if Var.UPDATES_CHANNEL == "None":
        return True
    try:
        member = await client.get_chat_member(Var.UPDATES_CHANNEL, chat_id)
        return member.status != "kicked"
    except UserNotParticipant:
        return False
    except Exception:
        return True


async def _gate_reply(client: Client, chat_id: int):
    await client.send_message(
        chat_id,
        "**Join the updates channel to use this bot.**",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Join Now 🔓", url=f"https://t.me/{Var.UPDATES_CHANNEL}")
        ]]),
    )


def _make_keyboard(stream_url: str, dl_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🖥 Stream", url=stream_url),
        InlineKeyboardButton("📥 Download", url=dl_url),
    ]])


def _file_info(m: Message):
    media = m.video or m.document or m.audio
    if not media:
        return None, None
    return getattr(media, "file_name", None), humanbytes(getattr(media, "file_size", 0))


LINK_MSG = (
    "<b>✅ Your links are ready!</b>\n\n"
    "<b>📂 File:</b> <i>{name}</i>\n"
    "<b>📦 Size:</b> <i>{size}</i>\n\n"
    "<b>🖥 Stream:</b> <code>{stream}</code>\n"
    "<b>📥 Download:</b> <code>{dl}</code>\n\n"
    "<i>Links are valid as long as the file exists.</i>"
)


@StreamBot.on_message(
    filters.private & (filters.document | filters.video | filters.audio),
    group=4,
)
async def private_receive_handler(client: Client, message: Message):
    user = message.from_user
    await _ensure_user(client, user.id, user.first_name)

    if not await _check_subscription(client, message.chat.id):
        await _gate_reply(client, message.chat.id)
        return

    try:
        log_msg     = await message.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = f"{Var.URL}watch/{log_msg.id}"
        dl_link     = f"{Var.URL}download/{log_msg.id}"
        file_name, file_size = _file_info(message)

        await log_msg.reply_text(
            f"**Requested by:** [{user.first_name}](tg://user?id={user.id})\n"
            f"**User ID:** `{user.id}`\n"
            f"**Stream:** {stream_link}",
            disable_web_page_preview=True,
        )

        await message.reply_text(
            LINK_MSG.format(name=file_name, size=file_size, stream=stream_link, dl=dl_link),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=_make_keyboard(stream_link, dl_link),
        )

    except FloodWait as e:
        wait = e.value if hasattr(e, "value") else e.x
        log.warning(f"FloodWait {wait}s from user {user.id}")
        await asyncio.sleep(wait)


@StreamBot.on_message(
    filters.channel & (filters.document | filters.video),
    group=-1,
)
async def channel_receive_handler(client: Client, broadcast: Message):
    if int(broadcast.chat.id) in Var.BANNED_CHANNELS:
        try:
            await client.leave_chat(broadcast.chat.id)
        except Exception:
            pass
        return

    try:
        log_msg     = await broadcast.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = f"{Var.URL}watch/{log_msg.id}"
        dl_link     = f"{Var.URL}download/{log_msg.id}"

        await log_msg.reply_text(
            f"**Channel:** `{broadcast.chat.title}`\n"
            f"**Channel ID:** `{broadcast.chat.id}`\n"
            f"**Stream:** {stream_link}",
        )

        await client.edit_message_reply_markup(
            chat_id=broadcast.chat.id,
            message_id=broadcast.id,
            reply_markup=_make_keyboard(stream_link, dl_link),
        )

    except FloodWait as e:
        wait = e.value if hasattr(e, "value") else e.x
        log.warning(f"FloodWait {wait}s from channel {broadcast.chat.id}")
        await asyncio.sleep(wait)
    except Exception as e:
        log.error(f"Channel handler error: {e}")
