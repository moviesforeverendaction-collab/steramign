# StreamBot - start.py
import logging

from pyrogram import filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Code_X_Mania.bot import StreamBot
from Code_X_Mania.utils.database import Database
from Code_X_Mania.utils.human_readable import humanbytes
from Code_X_Mania.vars import Var

log = logging.getLogger(__name__)
db  = Database(Var.DATABASE_URL, Var.SESSION_NAME)


async def _ensure_user(client, user_id: int, first_name: str):
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id)
        try:
            await client.send_message(
                Var.BIN_CHANNEL,
                f"**New User:** [{first_name}](tg://user?id={user_id})",
            )
        except Exception:
            pass


async def _check_subscription(client, chat_id: int) -> bool:
    if Var.UPDATES_CHANNEL == "None":
        return True
    try:
        member = await client.get_chat_member(Var.UPDATES_CHANNEL, chat_id)
        return member.status != "kicked"
    except UserNotParticipant:
        return False
    except Exception:
        return True


async def _gate_reply(client, chat_id: int):
    await client.send_message(
        chat_id,
        "**Join the updates channel to use this bot.**",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Join Now 🔓", url=f"https://t.me/{Var.UPDATES_CHANNEL}")
        ]]),
    )


@StreamBot.on_message(filters.command("start") & filters.private & ~filters.edited)
async def start_handler(client, message):
    user = message.from_user
    await _ensure_user(client, user.id, user.first_name)

    parts   = message.text.split("_", 1)
    payload = parts[1] if len(parts) > 1 else None

    if not await _check_subscription(client, message.chat.id):
        await _gate_reply(client, message.chat.id)
        return

    if payload is None:
        await message.reply_text(
            "<b>👋 Welcome to StreamBot!</b>\n\n"
            "<i>Send me any file — video, audio, or document — and I'll generate "
            "instant stream &amp; download links.</i>\n\n"
            "Use /help for more info.",
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Owner", url=f"https://t.me/{Var.OWNER_USERNAME}"),
            ]]),
        )
        return

    try:
        msg_id  = int(payload)
        get_msg = await client.get_messages(chat_id=Var.BIN_CHANNEL, message_ids=msg_id)

        media = get_msg.video or get_msg.document or get_msg.audio
        if not media:
            await message.reply_text("❌ File not found or has been deleted.")
            return

        file_name   = getattr(media, "file_name", "Unknown")
        file_size   = humanbytes(getattr(media, "file_size", 0))
        stream_link = f"{Var.URL}watch/{msg_id}"
        dl_link     = f"{Var.URL}download/{msg_id}"

        await message.reply_text(
            "<b>✅ Here are your links!</b>\n\n"
            f"<b>📂 File:</b> <i>{file_name}</i>\n"
            f"<b>📦 Size:</b> <i>{file_size}</i>\n\n"
            f"<b>🖥 Stream:</b> <code>{stream_link}</code>\n"
            f"<b>📥 Download:</b> <code>{dl_link}</code>\n\n"
            "<i>Links won't expire unless the file is deleted.</i>",
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🖥 Stream", url=stream_link),
                InlineKeyboardButton("📥 Download", url=dl_link),
            ]]),
        )
    except Exception as e:
        log.exception(e)
        await message.reply_text("❌ Something went wrong. Please try again.")


@StreamBot.on_message(filters.command("help") & filters.private & ~filters.edited)
async def help_handler(client, message):
    user = message.from_user
    await _ensure_user(client, user.id, user.first_name)

    if not await _check_subscription(client, message.chat.id):
        await _gate_reply(client, message.chat.id)
        return

    await message.reply_text(
        "<b>📖 How to use StreamBot</b>\n\n"
        "1. Send any <b>video, audio, or document</b> file directly here.\n"
        "2. Get an instant <b>stream link</b> (watch in browser) and <b>download link</b>.\n"
        "3. Share the links — they work for anyone!\n\n"
        "<b>Commands:</b>\n"
        "/start — Welcome message\n"
        "/help — This message\n\n"
        "<i>No file size limits. No expiry.</i>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
