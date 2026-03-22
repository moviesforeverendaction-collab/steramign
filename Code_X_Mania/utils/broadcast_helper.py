import asyncio
import traceback
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid


async def send_msg(user_id: int, message) -> tuple[int, str | None]:
    try:
        await message.forward(chat_id=user_id)
        return 200, None
    except FloodWait as e:
        wait = e.value if hasattr(e, "value") else e.x
        await asyncio.sleep(wait)
        return await send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : invalid peer id\n"
    except Exception:
        return 500, f"{user_id} : {traceback.format_exc()}\n"
