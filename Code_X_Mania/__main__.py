import sys
import glob
import asyncio
import logging
import importlib
from pathlib import Path

from aiohttp import web
from pyrogram import idle

from Code_X_Mania.bot import StreamBot
from Code_X_Mania.vars import Var
from Code_X_Mania.server import web_server
from Code_X_Mania.utils.database import Database

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
        if Path(path).stem == "__init__":
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
    log.info("Starting Telegram bot ...")
    await StreamBot.start()
    me = await StreamBot.get_me()
    log.info(f"Bot started: @{me.username}")

    db = Database(Var.DATABASE_URL, Var.SESSION_NAME)
    await db.ensure_indexes()
    log.info("Database indexes verified.")

    await load_plugins()

    log.info("Starting web server ...")
    runner = web.AppRunner(await web_server())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", Var.PORT).start()
    log.info(f"Web server live at {Var.URL}")

    log.info("=" * 60)
    log.info(f"  Bot   : {me.first_name} (@{me.username})")
    log.info(f"  URL   : {Var.URL}")
    log.info(f"  Owner : @{Var.OWNER_USERNAME}")
    log.info("=" * 60)

    await idle()


async def stop_services():
    log.info("Stopping ...")
    await StreamBot.stop()


def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    pending = asyncio.all_tasks(loop)
    if not pending:
        return
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        loop.run_until_complete(stop_services())
        log.info("Service stopped.")
    finally:
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            asyncio.set_event_loop(None)
            loop.close()
