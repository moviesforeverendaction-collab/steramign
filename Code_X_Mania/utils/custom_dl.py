# StreamBot - custom_dl.py
# Adapted from megadlbot_oss (Eyaadh) — thank you!

import math
from typing import Union, AsyncGenerator

from pyrogram import Client, raw, utils
from pyrogram.errors import AuthBytesInvalid
from pyrogram.file_id import FileId, FileType, ThumbnailSource
from pyrogram.session import Auth, Session
from pyrogram.types import Message

from ..bot import StreamBot


# ---------------------------------------------------------------------------
# Chunk helpers
# ---------------------------------------------------------------------------

async def chunk_size(length: int) -> int:
    """Power-of-two chunk size, clamped 4 KB – 1 MB for max throughput."""
    return 2 ** max(min(math.ceil(math.log2(length / 1024)), 10), 2) * 1024


async def offset_fix(offset: int, chunksize: int) -> int:
    return offset - (offset % chunksize)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class TGCustomYield:
    def __init__(self):
        self.main_bot: Client = StreamBot

    # --- File properties ---

    @staticmethod
    async def generate_file_properties(msg: Message) -> FileId:
        error_message = "This message has no downloadable media."
        available_media = (
            "audio", "document", "photo", "sticker",
            "animation", "video", "voice", "video_note",
        )

        if isinstance(msg, Message):
            for kind in available_media:
                media = getattr(msg, kind, None)
                if media is not None:
                    break
            else:
                raise ValueError(error_message)
        else:
            media = msg

        file_id_str = media if isinstance(media, str) else media.file_id
        file_id_obj = FileId.decode(file_id_str)

        setattr(file_id_obj, "file_size",  getattr(media, "file_size",  0))
        setattr(file_id_obj, "mime_type",  getattr(media, "mime_type",  ""))
        setattr(file_id_obj, "file_name",  getattr(media, "file_name",  ""))

        return file_id_obj

    # --- Media session (cached per DC) ---

    async def generate_media_session(self, client: Client, msg: Message) -> Session:
        data = await self.generate_file_properties(msg)

        media_session = client.media_sessions.get(data.dc_id)

        if media_session is None:
            if data.dc_id != await client.storage.dc_id():
                media_session = Session(
                    client,
                    data.dc_id,
                    await Auth(client, data.dc_id, await client.storage.test_mode()).create(),
                    await client.storage.test_mode(),
                    is_media=True,
                )
                await media_session.start()

                for _ in range(3):
                    exported_auth = await client.send(
                        raw.functions.auth.ExportAuthorization(dc_id=data.dc_id)
                    )
                    try:
                        await media_session.send(
                            raw.functions.auth.ImportAuthorization(
                                id=exported_auth.id,
                                bytes=exported_auth.bytes,
                            )
                        )
                        break
                    except AuthBytesInvalid:
                        continue
                else:
                    await media_session.stop()
                    raise AuthBytesInvalid
            else:
                media_session = Session(
                    client,
                    data.dc_id,
                    await client.storage.auth_key(),
                    await client.storage.test_mode(),
                    is_media=True,
                )
                await media_session.start()

            client.media_sessions[data.dc_id] = media_session

        return media_session

    # --- File location ---

    @staticmethod
    async def get_location(file_id: FileId):
        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            peer = (
                raw.types.InputPeerUser(
                    user_id=file_id.chat_id,
                    access_hash=file_id.chat_access_hash,
                )
                if file_id.chat_id > 0
                else (
                    raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                    if file_id.chat_access_hash == 0
                    else raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash,
                    )
                )
            )
            return raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
            )

        if file_type == FileType.PHOTO:
            return raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size,
            )

        return raw.types.InputDocumentFileLocation(
            id=file_id.media_id,
            access_hash=file_id.access_hash,
            file_reference=file_id.file_reference,
            thumb_size=file_id.thumbnail_size,
        )

    # --- Streaming generator ---

    async def yield_file(
        self,
        media_msg: Message,
        offset: int,
        first_part_cut: int,
        last_part_cut: int,
        part_count: int,
        chunk_size: int,
    ) -> AsyncGenerator[bytes, None]:
        client        = self.main_bot
        data          = await self.generate_file_properties(media_msg)
        media_session = await self.generate_media_session(client, media_msg)
        location      = await self.get_location(data)

        current_part = 1

        response = await media_session.send(
            raw.functions.upload.GetFile(
                location=location,
                offset=offset,
                limit=chunk_size,
            )
        )

        if not isinstance(response, raw.types.upload.File):
            return

        while current_part <= part_count:
            chunk = response.bytes
            if not chunk:
                break

            if part_count == 1:
                yield chunk[first_part_cut:last_part_cut]
                break
            elif current_part == 1:
                yield chunk[first_part_cut:]
            elif current_part == part_count:
                yield chunk[:last_part_cut]
            else:
                yield chunk

            offset += chunk_size
            current_part += 1

            response = await media_session.send(
                raw.functions.upload.GetFile(
                    location=location,
                    offset=offset,
                    limit=chunk_size,
                )
            )
