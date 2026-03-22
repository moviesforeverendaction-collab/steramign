from __future__ import annotations
from pyrogram import Client
from Code_X_Mania.vars import Var

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(
            name=Var.SESSION_NAME,
            api_id=Var.API_ID,
            api_hash=Var.API_HASH,
            bot_token=Var.BOT_TOKEN,
            sleep_threshold=Var.SLEEP_THRESHOLD,
            workers=Var.WORKERS or None,
            max_concurrent_transmissions=100,
        )
    return _client


class _LazyClientProxy:
    def __getattr__(self, name: str):
        return getattr(get_client(), name)

    def __repr__(self) -> str:
        return repr(get_client())


StreamBot = _LazyClientProxy()
