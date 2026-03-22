# StreamBot - entry point
import sys
import glob
import asyncio
import logging
import importlib
from pathlib import Path

from aiohttp import web
from pyrogram import idle

from .bot import StreamBot
from .vars import Var
from .server import web_server
from .utils.database import Database

# Detect uvloop AFTER all imports, then pass as loop_factory to asyncio.run().
# NEVER call asyncio.set_event_loop_policy() here — doing so creates a new loop
# before asyncio.run() does, which causes Pyrogram's Session recv_worker tasks
# to bind to a different loop → RuntimeError: "Future attached to a different loop".
try:
    import uvloop as _uvloop
    _loop_factory = _uvloop.new_event_loop
except ImportError:
    _uvloop = None
    _loop_factory = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

PLUGIN_GLOB = "Code_X_Mania/bot/plugins/*.py"


async def load_plugins():
    for path in sorted(glob.glob(PLUGIN_GLOB)):
        if Path(path).stem == "__init__":      # skip package marker
            continue
        plugin_name = Path(path).stem
        spec = importlib.util.spec_from_file_location(
            f"Code_X_Mania.bot.plugins.{plugin_name}", path
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[f"Code_X_Mania.bot.plugins.{plugin_name}"] = mod
        log.info(f"Loaded plugin: {plugin_name}")


async def start_services():
    log.info("Starting Telegram bot …")
    await StreamBot.start()
    me = await StreamBot.get_me()
    log.info(f"Bot started: @{me.username}")

    # Ensure MongoDB indexes exist (idempotent, safe every startup)
    db = Database(Var.DATABASE_URL, Var.SESSION_NAME)
    await db.ensure_indexes()
    log.info("Database indexes verified.")

    await load_plugins()

    log.info("Starting web server …")
    runner = web.AppRunner(await web_server())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", Var.PORT).start()
    log.info(f"Web server live at {Var.URL}")

    log.info("=" * 60)
    log.info(f"  Bot   : {me.first_name} (@{me.username})")
    log.info(f"  URL   : {Var.URL}")
    log.info(f"  Owner : @{Var.OWNER_USERNAME}")
    if _loop_factory:
        log.info("  Loop  : uvloop (fast)")
    log.info("=" * 60)

    await idle()


async def stop_services():
    log.info("Stopping …")
    await StreamBot.stop()


if __name__ == "__main__":
    try:
        if _loop_factory:
            # Python 3.12+: loop_factory ensures uvloop creates the SAME loop
            # that asyncio.run() uses — no cross-loop conflicts with Pyrogram.
            asyncio.run(start_services(), loop_factory=_loop_factory)
        else:
            asyncio.run(start_services())
    except KeyboardInterrupt:
        asyncio.run(stop_services())
        log.info("Service stopped.")
