from datetime import datetime

from icalendar import Calendar, Event

from icalendar_searcher import Searcher, peek


def test_check_empty():
    searcher = Searcher(start=datetime(1970, 1, 1), end=datetime.now())

    ## TODO: icalendar7 (not released yet) has some
    ## factory methods for creating valid VCALENDAR
    ## objects (IIRC).
    empty_calendar = Calendar()

    ## An empty calendar should yield nothing (currently
    ## the docstring says it should return None, but [] is probably
    ## equally acceptable)
    assert not searcher.check_component(empty_calendar)


def test_filter_component_types():
    searcher = Searcher(todo=True)
    cal = Calendar()
    comp = Event()
    comp["uid"] = "someuid"
    cal.add_component(comp)
    assert not searcher.check_component(cal)


def test_peek():
    assert peek(["a", "b", "c"])
    assert "b" in peek(["a", "b", "c"])
    assert peek([]) is False
    assert peek(range(1, 4))
    assert peek(range(0, 0)) is False
    mygen1 = (x for x in range(1, 8) if x > 2)
    mygen2 = (x for x in range(1, 8) if x < 0)
    assert next(peek(mygen1)) == 3
    assert peek(mygen2) is False
