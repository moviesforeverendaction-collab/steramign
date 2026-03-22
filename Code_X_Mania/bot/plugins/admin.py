# StreamBot - admin.py
import os
import time
import logging

import aiofiles
from pyrogram import filters
from pyrogram.types import Message

from Code_X_Mania.bot import StreamBot
from Code_X_Mania.utils.broadcast_helper import send_msg
from Code_X_Mania.utils.database import Database
from Code_X_Mania.utils.time_format import get_readable_time
from Code_X_Mania.vars import Var

log = logging.getLogger(__name__)
db  = Database(Var.DATABASE_URL, Var.SESSION_NAME)

OWNER_FILTER = filters.private & filters.user(Var.OWNER_ID) & ~filters.edited


# ── /status ──────────────────────────────────────────────────────────────────

@StreamBot.on_message(filters.command("status") & OWNER_FILTER)
async def status_handler(_, message: Message):
    total = await db.total_users_count()
    await message.reply_text(
        f"**Bot Status**\n\n"
        f"👥 Total users: `{total}`",
        parse_mode="Markdown",
        quote=True,
    )


# ── /broadcast ───────────────────────────────────────────────────────────────

@StreamBot.on_message(filters.command("broadcast") & OWNER_FILTER & filters.reply)
async def broadcast_handler(_, message: Message):
    broadcast_msg = message.reply_to_message
    all_users     = await db.get_all_users()
    total         = await db.total_users_count()

    status_msg = await message.reply_text(
        f"📡 Starting broadcast to `{total}` users…",
        parse_mode="Markdown",
        quote=True,
    )

    start_time = time.time()
    done = success = failed = 0
    log_lines = []

    async for user in all_users:
        code, msg = await send_msg(int(user["id"]), broadcast_msg)
        if code == 200:
            success += 1
        else:
            failed += 1
            if msg:
                log_lines.append(msg)
        if code == 400:
            await db.delete_user(user["id"])
        done += 1

        # Live progress every 50 users
        if done % 50 == 0:
            try:
                await status_msg.edit_text(
                    f"📡 Broadcasting… `{done}/{total}` — ✅ {success}  ❌ {failed}",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    elapsed = get_readable_time(time.time() - start_time)
    summary = (
        f"✅ **Broadcast complete** in `{elapsed}`\n\n"
        f"👥 Total: `{total}`\n"
        f"✅ Success: `{success}`\n"
        f"❌ Failed: `{failed}`"
    )

    await status_msg.delete()

    if log_lines:
        log_path = "broadcast_log.txt"
        async with aiofiles.open(log_path, "w") as f:
            await f.writelines(log_lines)
        await message.reply_document(
            document=log_path,
            caption=summary,
            parse_mode="Markdown",
            quote=True,
        )
        os.remove(log_path)
    else:
        await message.reply_text(summary, parse_mode="Markdown", quote=True)
