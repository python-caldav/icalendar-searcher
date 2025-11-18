from datetime import datetime

from icalendar import Calendar, Event
from icalendar.prop import vRecur

from icalendar_searcher import Searcher


def test_recurrence_simple_matches_exact_date() -> None:
    """Simple yearly recurrence should match when date range covers the first occurrence."""
    cal = Calendar()
    event = Event()
    event.add("uid", "yearly-event")
    event.add("summary", "New Year Celebration")
    event.add("dtstart", datetime(2025, 1, 1, 10, 0))
    event.add("dtend", datetime(2025, 1, 1, 12, 0))
    event.add("rrule", vRecur(FREQ="YEARLY"))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 2, 0, 0),
    )
    assert searcher.check_component(cal)


def test_recurrence_simple_matches_future_occurrence() -> None:
    """Simple yearly recurrence should match when date range covers a future occurrence."""
    cal = Calendar()
    event = Event()
    event.add("uid", "yearly-event")
    event.add("summary", "New Year Celebration")
    event.add("dtstart", datetime(2025, 1, 1, 10, 0))
    event.add("dtend", datetime(2025, 1, 1, 12, 0))
    event.add("rrule", vRecur(FREQ="YEARLY"))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2026, 1, 1, 0, 0),
        end=datetime(2026, 1, 2, 0, 0),
    )
    assert searcher.check_component(cal)


def test_recurrence_simple_matches_open_ended_range() -> None:
    """Simple yearly recurrence should match with an open-ended date range."""
    cal = Calendar()
    event = Event()
    event.add("uid", "yearly-event")
    event.add("summary", "New Year Celebration")
    event.add("dtstart", datetime(2025, 1, 1, 10, 0))
    event.add("dtend", datetime(2025, 1, 1, 12, 0))
    event.add("rrule", vRecur(FREQ="YEARLY"))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2027, 12, 31, 23, 59),
    )
    assert searcher.check_component(cal)


def test_recurrence_simple_matches_no_range() -> None:
    """Simple yearly recurrence should match when no date range is specified."""
    cal = Calendar()
    event = Event()
    event.add("uid", "yearly-event")
    event.add("summary", "New Year Celebration")
    event.add("dtstart", datetime(2025, 1, 1, 10, 0))
    event.add("dtend", datetime(2025, 1, 1, 12, 0))
    event.add("rrule", vRecur(FREQ="YEARLY"))
    cal.add_component(event)

    searcher = Searcher(event=True)
    assert searcher.check_component(cal)


def test_recurrence_exception_original_summary_matches() -> None:
    """Recurrence with exception should match when filtering on original summary."""
    cal = Calendar()
    event_base = Event()
    event_base.add("uid", "weekly-meeting")
    event_base.add("summary", "Weekly Team Meeting")
    event_base.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event_base.add("dtend", datetime(2025, 1, 6, 11, 0))
    event_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event_base)

    event_exception = Event()
    event_exception.add("uid", "weekly-meeting")
    event_exception.add("summary", "Special Planning Session")
    event_exception.add("dtstart", datetime(2025, 1, 13, 10, 0))
    event_exception.add("dtend", datetime(2025, 1, 13, 11, 0))
    event_exception.add("recurrence-id", datetime(2025, 1, 13, 10, 0))
    cal.add_component(event_exception)

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "Weekly Team Meeting", operator="==")
    assert searcher.check_component(cal), "Should match base event with original summary"


def test_recurrence_exception_original_summary_matches_first_occurrence() -> None:
    """Recurrence with exception should match original summary with range covering first occurrence."""
    cal = Calendar()
    event_base = Event()
    event_base.add("uid", "weekly-meeting")
    event_base.add("summary", "Weekly Team Meeting")
    event_base.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event_base.add("dtend", datetime(2025, 1, 6, 11, 0))
    event_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event_base)

    event_exception = Event()
    event_exception.add("uid", "weekly-meeting")
    event_exception.add("summary", "Special Planning Session")
    event_exception.add("dtstart", datetime(2025, 1, 13, 10, 0))
    event_exception.add("dtend", datetime(2025, 1, 13, 11, 0))
    event_exception.add("recurrence-id", datetime(2025, 1, 13, 10, 0))
    cal.add_component(event_exception)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 6, 0, 0),
        end=datetime(2025, 1, 7, 0, 0),
    )
    searcher.add_property_filter("SUMMARY", "Weekly Team Meeting", operator="==")
    assert searcher.check_component(cal)


def test_recurrence_exception_original_summary_not_match_exception_only() -> None:
    """Recurrence with exception should NOT match original summary when range only covers exception."""
    cal = Calendar()
    event_base = Event()
    event_base.add("uid", "weekly-meeting")
    event_base.add("summary", "Weekly Team Meeting")
    event_base.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event_base.add("dtend", datetime(2025, 1, 6, 11, 0))
    event_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event_base)

    event_exception = Event()
    event_exception.add("uid", "weekly-meeting")
    event_exception.add("summary", "Special Planning Session")
    event_exception.add("dtstart", datetime(2025, 1, 13, 10, 0))
    event_exception.add("dtend", datetime(2025, 1, 13, 11, 0))
    event_exception.add("recurrence-id", datetime(2025, 1, 13, 10, 0))
    cal.add_component(event_exception)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 13, 0, 0),
        end=datetime(2025, 1, 14, 0, 0),
    )
    searcher.add_property_filter("SUMMARY", "Weekly Team Meeting", operator="==")
    assert not searcher.check_component(cal), "Should not match when range only covers exception"


def test_recurrence_exception_modified_summary_matches() -> None:
    """Recurrence with exception should match when filtering on modified summary."""
    cal = Calendar()
    event_base = Event()
    event_base.add("uid", "weekly-meeting")
    event_base.add("summary", "Weekly Team Meeting")
    event_base.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event_base.add("dtend", datetime(2025, 1, 6, 11, 0))
    event_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event_base)

    event_exception = Event()
    event_exception.add("uid", "weekly-meeting")
    event_exception.add("summary", "Special Planning Session")
    event_exception.add("dtstart", datetime(2025, 1, 13, 10, 0))
    event_exception.add("dtend", datetime(2025, 1, 13, 11, 0))
    event_exception.add("recurrence-id", datetime(2025, 1, 13, 10, 0))
    cal.add_component(event_exception)

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "Special Planning Session", operator="==")
    assert searcher.check_component(cal), "Should match the exception with modified summary"


def test_recurrence_exception_modified_summary_matches_with_range() -> None:
    """Recurrence with exception should match modified summary when range covers exception."""
    cal = Calendar()
    event_base = Event()
    event_base.add("uid", "weekly-meeting")
    event_base.add("summary", "Weekly Team Meeting")
    event_base.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event_base.add("dtend", datetime(2025, 1, 6, 11, 0))
    event_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event_base)

    event_exception = Event()
    event_exception.add("uid", "weekly-meeting")
    event_exception.add("summary", "Special Planning Session")
    event_exception.add("dtstart", datetime(2025, 1, 13, 10, 0))
    event_exception.add("dtend", datetime(2025, 1, 13, 11, 0))
    event_exception.add("recurrence-id", datetime(2025, 1, 13, 10, 0))
    cal.add_component(event_exception)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 13, 0, 0),
        end=datetime(2025, 1, 14, 0, 0),
    )
    searcher.add_property_filter("SUMMARY", "Special Planning Session", operator="==")
    assert searcher.check_component(cal)


def test_recurrence_exception_modified_summary_not_match_wrong_range() -> None:
    """Recurrence with exception should NOT match modified summary when range doesn't cover exception."""
    cal = Calendar()
    event_base = Event()
    event_base.add("uid", "weekly-meeting")
    event_base.add("summary", "Weekly Team Meeting")
    event_base.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event_base.add("dtend", datetime(2025, 1, 6, 11, 0))
    event_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event_base)

    event_exception = Event()
    event_exception.add("uid", "weekly-meeting")
    event_exception.add("summary", "Special Planning Session")
    event_exception.add("dtstart", datetime(2025, 1, 13, 10, 0))
    event_exception.add("dtend", datetime(2025, 1, 13, 11, 0))
    event_exception.add("recurrence-id", datetime(2025, 1, 13, 10, 0))
    cal.add_component(event_exception)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 6, 0, 0),
        end=datetime(2025, 1, 7, 0, 0),
    )
    searcher.add_property_filter("SUMMARY", "Special Planning Session", operator="==")
    assert not searcher.check_component(cal), "Should not match when exception is outside date range"
