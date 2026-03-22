def humanbytes(size: int) -> str:
    if not size:
        return "0 B"
    power = 1024
    labels = ["B", "KB", "MB", "GB", "TB"]
    n = 0
    while size >= power and n < len(labels) - 1:
        size /= power
        n += 1
    return f"{round(size, 2)} {labels[n]}"
