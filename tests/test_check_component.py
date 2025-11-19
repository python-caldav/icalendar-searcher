from datetime import datetime

import pytest
from icalendar import Calendar, Event, Todo

from icalendar_searcher import Searcher, _iterable_or_false


def test_include_completed() -> None:
    ## Status Needs Action
    task_sna = Todo()
    task_sna["STATUS"] = "NEEDS-ACTION"

    ## No Status
    task_ns = Todo()

    ## No Status, Completed
    task_nsc = Todo()
    task_nsc["COMPLETED"] = datetime(2000, 1, 2)

    ## Status cancelled
    task_sc = Todo()
    task_sc["STATUS"] = "CANCELLED"

    for component in (task_sna, task_ns, task_nsc, task_sc):
        component["uid"] = "123"

    onlypending = Searcher(todo=True)
    all1 = Searcher(todo=True, include_completed=True)
    all2 = Searcher()
    for component in (task_nsc, task_sc):
        assert not onlypending.check_component(component)
        assert all1.check_component(component)
        assert all2.check_component(component)

    for component in (task_ns, task_sna):
        assert onlypending.check_component(component)
        assert all1.check_component(component)
        assert all2.check_component(component)


def test_check_empty() -> None:
    """Test that an empty calendar (no components) raises a ValueError."""
    searcher = Searcher(start=datetime(1970, 1, 1), end=datetime.now())

    # Create an empty calendar (no VEVENT, VTODO, or VJOURNAL components)
    empty_calendar = Calendar()

    # An empty calendar should raise a ValueError
    # See _validate_and_normalize_component() at line 498
    with pytest.raises(ValueError, match="Empty component"):
        searcher.check_component(empty_calendar)


def test_filter_component_types() -> None:
    cal = Calendar()
    comp = Event()
    comp["uid"] = "someuid"
    cal.add_component(comp)
    for searcher in (
        Searcher(todo=True),
        Searcher(event=False),
        Searcher(event=False, journal=True),
    ):
        assert not searcher.check_component(cal)
    for searcher in (Searcher(), Searcher(event=True), Searcher(todo=False)):
        assert searcher.check_component(cal)


## _iterable_or_false() was defined to support return values evaluating into False,
## but still support generators
def test_iterable_or_false() -> None:
    assert _iterable_or_false(["a", "b", "c"])
    assert "b" in _iterable_or_false(["a", "b", "c"])
    assert _iterable_or_false([]) is False
    assert _iterable_or_false(range(1, 4))
    assert _iterable_or_false(range(0, 0)) is False
    mygen1 = (x for x in range(1, 8) if x > 2)
    mygen2 = (x for x in range(1, 8) if x < 0)
    assert next(_iterable_or_false(mygen1)) == 3
    assert _iterable_or_false(mygen2) is False


def test_yule_tree1() -> None:
    """
    In caldav, the basic usage example stopped working
    """
    data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//python-caldav//caldav//en_DK
BEGIN:VTODO
CATEGORIES:outdoor
DTSTAMP:20251119T133355Z
DTSTART;VALUE=DATE:20201213
DUE;VALUE=DATE:20201220
PRIORITY:2
RRULE:FREQ=YEARLY
STATUS:NEEDS-ACTION
SUMMARY:Chop down a tree and drag it into the living room
UID:652e3718-c54c-11f0-9203-1c1bb5134174
END:VTODO
END:VCALENDAR"""
    cal = Calendar.from_ical(data)
    for prop_filter in (("categories", "outdoor", "=="), ("categories", "out")):
        for searcher in (Searcher(), Searcher(todo=True)):
            searcher.add_property_filter(*prop_filter)
            assert searcher._check_property_filters(cal.subcomponents[0])
            assert searcher.check_component(cal)
    for prop_filter in (("categories", "out", "=="), ("categories", "outdoors")):
        for searcher in (Searcher(), Searcher(event=True), Searcher(todo=True)):
            searcher.add_property_filter(*prop_filter)
            assert not searcher._check_property_filters(cal.subcomponents[0])
            assert not searcher.check_component(cal)


def test_yule_tree2() -> None:
    """
    categories are difficult
    """
    data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//python-caldav//caldav//en_DK
BEGIN:VTODO
CATEGORIES:outdoor,family,winter
DTSTAMP:20251119T133355Z
DTSTART;VALUE=DATE:20201213
DUE;VALUE=DATE:20201220
PRIORITY:2
RRULE:FREQ=YEARLY
STATUS:NEEDS-ACTION
SUMMARY:Chop down a tree and drag it into the living room
UID:652e3718-c54c-11f0-9203-1c1bb5134174
END:VTODO
END:VCALENDAR"""
    cal = Calendar.from_ical(data)
    for prop_filter in (
        ("categories", ["family", "outdoor", "winter"], "=="),
        ("categories", "family,outdoor,winter", "=="),
        ("categories", "winter,outdoor,family", "=="),
        ("categories", "winter,outdoor"),
        ("categories", ("winter", "outdoor")),
        ("categories", "outdoor", "=="),
        ("categories", "out"),
    ):
        for searcher in (Searcher(), Searcher(todo=True)):
            searcher.add_property_filter(*prop_filter)
            assert searcher._check_property_filters(cal.subcomponents[0])
            assert searcher.check_component(cal)
    for prop_filter in (
        ("categories", "out", "=="),
        ("categories", "outdoors"),
        ("categories", "outdoor,summer"),
        ("categories", ("outdoor,winter"), "=="),
    ):
        for searcher in (Searcher(), Searcher(event=True), Searcher(todo=True)):
            searcher.add_property_filter(*prop_filter)
            assert not searcher._check_property_filters(cal.subcomponents[0])
            assert not searcher.check_component(cal)
