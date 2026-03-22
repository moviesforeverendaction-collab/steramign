import secrets
import mimetypes
import urllib.parse
from pathlib import Path

import aiofiles

from Code_X_Mania.vars import Var
from Code_X_Mania.bot import StreamBot
from Code_X_Mania.utils.custom_dl import TGCustomYield
from Code_X_Mania.utils.human_readable import humanbytes

TEMPLATE_DIR = Path(__file__).parent.parent / "template"

VIDEO_TYPES = {
    "video/mp4", "video/webm", "video/ogg",
    "video/x-matroska", "video/avi", "video/quicktime",
    "video/x-msvideo", "video/mpeg",
}
AUDIO_TYPES = {
    "audio/mpeg", "audio/mp4", "audio/ogg",
    "audio/wav", "audio/x-wav", "audio/flac",
    "audio/aac", "audio/webm",
}


def _fill(template: str, **kwargs) -> str:
    for key, value in kwargs.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


async def fetch_properties(message_id: int):
    media_msg  = await StreamBot.get_messages(Var.BIN_CHANNEL, message_id)
    file_props = await TGCustomYield().generate_file_properties(media_msg)
    file_name  = file_props.file_name or f"{secrets.token_hex(4)}.bin"
    mime_type  = (
        file_props.mime_type
        or mimetypes.guess_type(file_name)[0]
        or "application/octet-stream"
    )
    file_size = humanbytes(file_props.file_size)
    return file_name, mime_type, file_size


async def render_page(message_id: int) -> str:
    file_name, mime_type, file_size = await fetch_properties(message_id)
    src        = urllib.parse.urljoin(Var.URL, str(message_id))
    mime_lower = mime_type.lower()

    if mime_lower in VIDEO_TYPES or mime_lower in AUDIO_TYPES:
        tag = "video" if mime_lower in VIDEO_TYPES else "audio"
        async with aiofiles.open(TEMPLATE_DIR / "req.html", encoding="utf-8") as f:
            template = await f.read()
        return _fill(
            template,
            TITLE=f"{'Watch' if tag == 'video' else 'Play'} — {file_name}",
            FILENAME=file_name,
            SRC=src,
            TAG=tag,
            MIME=mime_type,
        )
    else:
        async with aiofiles.open(TEMPLATE_DIR / "dl.html", encoding="utf-8") as f:
            template = await f.read()
        return _fill(
            template,
            TITLE=f"Download — {file_name}",
            FILENAME=file_name,
            SRC=src,
            FILESIZE=file_size,
        )
