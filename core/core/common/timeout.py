from datetime import timedelta


def timedelta_to_milliseconds(delta: timedelta) -> int:
    return int(delta.total_seconds() * 1e3)
