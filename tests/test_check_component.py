from datetime import datetime

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
    searcher = Searcher(start=datetime(1970, 1, 1), end=datetime.now())

    ## TODO: icalendar7 (not released yet) has some
    ## factory methods for creating valid VCALENDAR
    ## objects (IIRC).
    empty_calendar = Calendar()

    ## An empty calendar should yield nothing (currently
    ## the docstring says it should return None, but [] is probably
    ## equally acceptable)
    assert not searcher.check_component(empty_calendar)


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
