from datetime import timedelta

from core.common.timedelta_converter import timedelta_to_milliseconds, timedelta_to_seconds


def test_timedelta_to_milliseconds():
    """
    GIVEN: A timedelta object

    WHEN: Calling `timedelta_to_milliseconds`

    THEN: The timedelta is converted to correct amount of milliseconds taking all timedelta components into account
    AND: The result is an integer
    """
    timeout = timedelta(weeks=1, days=1, hours=2, minutes=3, seconds=4, milliseconds=5)

    result = timedelta_to_milliseconds(timeout)

    assert result == 1 * 7 * 24 * 60 * 60 * 1000 + \
           1 * 24 * 60 * 60 * 1000 + \
           2 * 60 * 60 * 1000 + \
           3 * 60 * 1000 + \
           4 * 1000 + \
           5

    assert isinstance(result, int)


def test_timedelta_to_seconds():
    """
    GIVEN: A timedelta object

    WHEN: Calling `timedelta_to_seconds`

    THEN: The timedelta is converted to correct amount of seconds taking all timedelta components into account
    AND: The result is a float
    """
    timeout = timedelta(weeks=1, days=1, hours=2, minutes=3, seconds=4, milliseconds=5)

    result = timedelta_to_seconds(timeout)

    assert result == \
           1 * 7 * 24 * 60 * 60 + \
           1 * 24 * 60 * 60 + \
           2 * 60 * 60 + \
           3 * 60 + \
           4 + \
           5 / 1000

    assert isinstance(result, float)
