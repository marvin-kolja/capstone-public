from datetime import timedelta

from core.common.timeout import timedelta_to_milliseconds


def test_timedelta_to_milliseconds():
    """
    GIVEN: A timedelta object

    WHEN: Calling `timedelta_to_milliseconds`

    THEN: The timedelta is converted to correct amount of milliseconds taking all timedelta components into account
    AND: The result is an integer
    """
    timeout = timedelta(days=1, hours=2, minutes=3, seconds=4, milliseconds=5)

    result = timedelta_to_milliseconds(timeout)

    assert result == 1 * 24 * 60 * 60 * 1000 + \
           2 * 60 * 60 * 1000 + \
           3 * 60 * 1000 + \
           4 * 1000 + \
           5

    assert isinstance(result, int)
