from datetime import timedelta

from pydantic import BaseModel

from pydantic_settings_utils.duration import (
    Duration,
    human_time_to_timedelta,
    timedelta_to_human_time,
)


def test_human_time_to_timedelta():
    for i in range(100):
        assert human_time_to_timedelta(f"{i}d") == timedelta(days=i)
        assert human_time_to_timedelta(f"{i}h") == timedelta(hours=i)
        assert human_time_to_timedelta(f"{i}m") == timedelta(minutes=i)
        assert human_time_to_timedelta(f"{i}s") == timedelta(seconds=i)

    for d, h, m, s in zip(range(1, 11), range(11, 21), range(21, 31), range(31, 41)):
        assert human_time_to_timedelta(f"{d}d{h}h{m}m{s}s") == timedelta(
            days=d, hours=h, minutes=m, seconds=s
        )


def test_timedelta_to_human_time():
    assert timedelta_to_human_time(timedelta(days=0)) == "0s"
    assert timedelta_to_human_time(timedelta(hours=0)) == "0s"
    assert timedelta_to_human_time(timedelta(minutes=0)) == "0s"
    assert timedelta_to_human_time(timedelta(seconds=0)) == "0s"

    for i in range(1, 23):
        assert timedelta_to_human_time(timedelta(days=i)) == f"{i}d"
        assert timedelta_to_human_time(timedelta(hours=i)) == f"{i}h"
        assert timedelta_to_human_time(timedelta(minutes=i)) == f"{i}m"
        assert timedelta_to_human_time(timedelta(seconds=i)) == f"{i}s"

    assert timedelta_to_human_time(timedelta(hours=25)) == "1d1h"
    assert timedelta_to_human_time(timedelta(minutes=61)) == "1h1m"
    assert timedelta_to_human_time(timedelta(minutes=61)) == "1h1m"
    assert timedelta_to_human_time(timedelta(seconds=61)) == "1m1s"
    assert timedelta_to_human_time(timedelta(seconds=90061)) == "1d1h1m1s"

    for d, h, m, s in zip(range(1, 11), range(11, 21), range(21, 31), range(31, 41)):
        assert (
            timedelta_to_human_time(timedelta(days=d, hours=h, minutes=m, seconds=s))
            == f"{d}d{h}h{m}m{s}s"
        )


def test_duration_type():
    class C(BaseModel):
        d: Duration

    c = C(d="1d1h1m1s")  # type: ignore

    assert c.d == timedelta(days=1, hours=1, minutes=1, seconds=1)
    assert c.model_dump()["d"] == "1d1h1m1s"
    assert c.model_dump_json() == '{"d":"1d1h1m1s"}'
