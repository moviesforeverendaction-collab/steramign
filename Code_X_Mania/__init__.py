# StreamBot - bot client
#
# ROOT CAUSE OF THE BUG:
# Pyrogram's Client spawns internal asyncio Tasks the moment it is
# constructed.  If the Client is built at *import time* (module level),
# those tasks are attached to whatever loop Python happens to have at
# that point.  asyncio.run() then creates a brand-new event loop, so the
# pre-existing tasks are bound to a *different* loop – hence:
#
#   RuntimeError: … got Future … attached to a different loop
#
# FIX:
# Never construct the Client at module level.  Instead expose a lazy
# singleton via get_client() that is called for the first time only
# after asyncio.run() has set up its loop (i.e. from inside a coroutine).
# A transparent _LazyClientProxy keeps all existing `from ..bot import
# StreamBot` call-sites working without any further changes.

from __future__ import annotations
from pyrogram import Client
from ..vars import Var

_client: Client | None = None


def get_client() -> Client:
    """Return the singleton Pyrogram Client, creating it on first call.

    Must be called from within a running asyncio event-loop.
    """
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
    """Transparent proxy – forwards every attribute access to the real Client."""

    def __getattr__(self, name: str):
        return getattr(get_client(), name)

    def __repr__(self) -> str:
        return repr(get_client())


# All existing `from ..bot import StreamBot` imports continue to work.
StreamBot = _LazyClientProxy()
