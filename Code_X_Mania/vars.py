import os
from dotenv import load_dotenv

load_dotenv()


class Var:
    API_ID          = int(os.getenv("API_ID"))
    API_HASH        = str(os.getenv("API_HASH"))
    BOT_TOKEN       = str(os.getenv("BOT_TOKEN"))
    SESSION_NAME    = str(os.getenv("SESSION_NAME", "StreamBot"))

    WORKERS         = int(os.getenv("WORKERS", "80"))
    SLEEP_THRESHOLD = int(os.getenv("SLEEP_THRESHOLD", "1800"))

    BIN_CHANNEL     = int(os.getenv("BIN_CHANNEL"))
    _owner_raw      = os.getenv("OWNER_ID", "")
    OWNER_ID        = int(_owner_raw) if _owner_raw.lstrip("-").isdigit() else 0
    OWNER_USERNAME  = str(os.getenv("OWNER_USERNAME", ""))
    UPDATES_CHANNEL = str(os.getenv("UPDATES_CHANNEL", "None"))
    BANNED_CHANNELS = list(
        set(int(x) for x in str(os.getenv("BANNED_CHANNELS", "0")).split() if x.lstrip("-").isdigit())
    )

    PORT      = int(os.getenv("PORT", "8080"))
    _raw_fqdn = os.getenv("FQDN") or os.getenv("RAILWAY_PUBLIC_DOMAIN") or f"0.0.0.0:{os.getenv('PORT', '8080')}"
    FQDN      = _raw_fqdn.removeprefix("https://").removeprefix("http://").rstrip("/")
    _scheme   = "https" if (os.getenv("RAILWAY_PUBLIC_DOMAIN") or os.getenv("FQDN", "").startswith("https")) else "http"
    URL       = f"{_scheme}://{FQDN}/"

    DATABASE_URL = str(os.getenv("DATABASE_URL"))
