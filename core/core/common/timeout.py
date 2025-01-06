from datetime import timedelta


def timedelta_to_seconds(delta: timedelta) -> float:
    return delta.total_seconds()


def timedelta_to_milliseconds(delta: timedelta) -> int:
    return int(timedelta_to_seconds(delta) * 1e3)
