# StreamBot - entry point
import sys
import glob
import asyncio
import logging
import importlib
from pathlib import Path

# Use uvloop for much faster event loop if available (Linux/macOS)
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

from aiohttp import web
from pyrogram import idle

from .bot import StreamBot
from .vars import Var
from .server import web_server

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
    for path in glob.glob(PLUGIN_GLOB):
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

    await load_plugins()

    log.info("Starting web server …")
    runner = web.AppRunner(await web_server())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", Var.PORT).start()
    log.info(f"Web server live at {Var.URL}")

    log.info("=" * 60)
    log.info(f"  Bot      : {me.first_name} (@{me.username})")
    log.info(f"  URL      : {Var.URL}")
    log.info(f"  Owner    : @{Var.OWNER_USERNAME}")
    log.info("=" * 60)

    await idle()


async def stop_services():
    log.info("Stopping …")
    await StreamBot.stop()


if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        asyncio.run(stop_services())
        log.info("Service stopped.")
