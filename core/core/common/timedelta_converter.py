from datetime import timedelta


def timedelta_to_seconds_precise(delta: timedelta) -> float:
    """
    Converts a timedelta object to seconds.

    The result may be a floating-point number for subsecond microsecond precision.

    :param delta: The timedelta object to convert
    :return: Floating-point number representing the seconds
    """

    return delta.total_seconds()


def timedelta_to_seconds(delta: timedelta) -> int:
    """
    Converts a timedelta object to seconds.

    Microseconds are truncated

    :param delta: The timedelta object to convert

    :return: Integer representing the seconds
    """
    return int(timedelta_to_seconds_precise(delta))


def timedelta_to_milliseconds_precise(delta: timedelta) -> float:
    """
    Converts a timedelta object to milliseconds.

    The result may be a floating-point number for submillisecond microsecond precision.

    :param delta: The timedelta object to convert

    :return: Floating-point number representing the milliseconds
    """
    return timedelta_to_seconds_precise(delta) * 1e3


def timedelta_to_milliseconds(delta: timedelta) -> int:
    """
    Converts a timedelta object to milliseconds.

    Microseconds are truncated

    :param delta: The timedelta object to convert

    :return: Integer representing the milliseconds
    """
    return int(timedelta_to_milliseconds_precise(delta))
