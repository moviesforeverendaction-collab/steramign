def get_readable_time(seconds: float) -> str:
    seconds = int(seconds)
    days, seconds  = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, secs  = divmod(seconds, 60)
    parts = []
    if days:    parts.append(f"{days}d")
    if hours:   parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
