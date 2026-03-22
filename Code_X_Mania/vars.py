# StreamBot - vars.py
import os
from dotenv import load_dotenv

load_dotenv()


class Var:
    # --- Telegram Credentials ---
    API_ID        = int(os.getenv("API_ID"))
    API_HASH      = str(os.getenv("API_HASH"))
    BOT_TOKEN     = str(os.getenv("BOT_TOKEN"))
    SESSION_NAME  = str(os.getenv("SESSION_NAME", "StreamBot"))

    # --- Performance (no artificial limits) ---
    # 0 = let Kurigram decide (uses all cores); set higher e.g. 200 for more parallelism
    WORKERS         = int(os.getenv("WORKERS", "0"))
    # Auto-sleep on FloodWait up to 30 min; anything above raises the exception
    SLEEP_THRESHOLD = int(os.getenv("SLEEP_THRESHOLD", "1800"))

    # --- Bot Config ---
    BIN_CHANNEL     = int(os.getenv("BIN_CHANNEL"))
    OWNER_ID        = str(os.getenv("OWNER_ID", ""))
    OWNER_USERNAME  = str(os.getenv("OWNER_USERNAME", ""))
    UPDATES_CHANNEL = str(os.getenv("UPDATES_CHANNEL", "None"))
    BANNED_CHANNELS = list(
        set(int(x) for x in str(os.getenv("BANNED_CHANNELS", "0")).split() if x.lstrip("-").isdigit())
    )

    # --- Web Server ---
    PORT         = int(os.getenv("PORT", "8080"))
    FQDN         = str(os.getenv("FQDN", os.getenv("RAILWAY_PUBLIC_DOMAIN", f"0.0.0.0:{os.getenv('PORT','8080')}")))
    # Use https if Railway provides domain, else http
    _scheme      = "https" if os.getenv("RAILWAY_PUBLIC_DOMAIN") or os.getenv("FQDN", "").startswith("https") else "http"
    URL          = f"{_scheme}://{FQDN}/"

    # --- Database ---
    DATABASE_URL = str(os.getenv("DATABASE_URL"))
