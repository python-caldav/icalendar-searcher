"""
Tests for handling date-only (all-day) events and todos.

When DTSTART, DTEND, or DUE are dates (not datetimes), special handling
is required for time range comparisons.
"""

from datetime import date, datetime

from icalendar import Calendar, Event, Todo

from icalendar_searcher import Searcher


def test_all_day_event_matches_date_range() -> None:
    """All-day event (date-only DTSTART) should match when date range covers it."""
    cal = Calendar()
    event = Event()
    event.add("uid", "allday-event")
    event.add("summary", "All Day Event")
    event.add("dtstart", date(2025, 1, 15))  # Date, not datetime
    event.add("dtend", date(2025, 1, 16))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 16, 0, 0),
    )
    result = searcher.check_component(cal)
    assert result, "All-day event should match date range covering it"


def test_all_day_event_matches_datetime_range_spanning() -> None:
    """All-day event should match when datetime range spans across it."""
    cal = Calendar()
    event = Event()
    event.add("uid", "allday-event")
    event.add("summary", "All Day Event")
    event.add("dtstart", date(2025, 1, 15))
    event.add("dtend", date(2025, 1, 16))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 14, 12, 0),
        end=datetime(2025, 1, 16, 12, 0),
    )
    result = searcher.check_component(cal)
    assert result, "All-day event should match range spanning it"


def test_all_day_event_not_match_before_range() -> None:
    """All-day event should not match when it's before the search range."""
    cal = Calendar()
    event = Event()
    event.add("uid", "allday-event")
    event.add("summary", "All Day Event")
    event.add("dtstart", date(2025, 1, 10))
    event.add("dtend", date(2025, 1, 11))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 20, 0, 0),
    )
    result = searcher.check_component(cal)
    assert not result, "All-day event before range should not match"


def test_all_day_event_not_match_after_range() -> None:
    """All-day event should not match when it's after the search range."""
    cal = Calendar()
    event = Event()
    event.add("uid", "allday-event")
    event.add("summary", "All Day Event")
    event.add("dtstart", date(2025, 1, 25))
    event.add("dtend", date(2025, 1, 26))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 10, 0, 0),
        end=datetime(2025, 1, 15, 0, 0),
    )
    result = searcher.check_component(cal)
    assert not result, "All-day event after range should not match"


def test_all_day_event_single_day() -> None:
    """Single-day all-day event (no DTEND) should match."""
    cal = Calendar()
    event = Event()
    event.add("uid", "allday-event")
    event.add("summary", "Single Day Event")
    event.add("dtstart", date(2025, 1, 15))
    # No DTEND - single day event
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 16, 0, 0),
    )
    result = searcher.check_component(cal)
    assert result, "Single-day all-day event should match"


def test_all_day_event_at_range_boundary_start() -> None:
    """All-day event at the start boundary of range should match."""
    cal = Calendar()
    event = Event()
    event.add("uid", "allday-event")
    event.add("summary", "Boundary Event")
    event.add("dtstart", date(2025, 1, 15))
    event.add("dtend", date(2025, 1, 16))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 20, 0, 0),
    )
    result = searcher.check_component(cal)
    assert result, "All-day event at start boundary should match"


def test_all_day_event_at_range_boundary_end() -> None:
    """All-day event at the end boundary of range should match."""
    cal = Calendar()
    event = Event()
    event.add("uid", "allday-event")
    event.add("summary", "Boundary Event")
    event.add("dtstart", date(2025, 1, 19))
    event.add("dtend", date(2025, 1, 20))
    cal.add_component(event)

    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 20, 0, 0),
    )
    result = searcher.check_component(cal)
    assert result, "All-day event at end boundary should match"


def test_todo_with_date_only_dtstart() -> None:
    """Todo with date-only DTSTART should work with datetime range."""
    task = Todo()
    task.add("uid", "task123")
    task.add("summary", "All-day task")
    task.add("dtstart", date(2025, 1, 15))

    searcher = Searcher(
        todo=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 16, 0, 0),
    )
    result = searcher.check_component(task)
    assert result, "Todo with date-only DTSTART should match"


def test_todo_with_date_only_due() -> None:
    """Todo with date-only DUE should work with datetime range."""
    task = Todo()
    task.add("uid", "task123")
    task.add("summary", "Task with due date")
    task.add("due", date(2025, 1, 15))

    searcher = Searcher(
        todo=True,
        start=datetime(2025, 1, 10, 0, 0),
        end=datetime(2025, 1, 20, 0, 0),
    )
    result = searcher.check_component(task)
    assert result, "Todo with date-only DUE should match"


def test_all_day_event_multi_day() -> None:
    """Multi-day all-day event should match range overlapping any part."""
    cal = Calendar()
    event = Event()
    event.add("uid", "multiday")
    event.add("summary", "Conference")
    event.add("dtstart", date(2025, 1, 15))
    event.add("dtend", date(2025, 1, 20))  # 5-day event
    cal.add_component(event)

    # Search for middle day
    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 17, 0, 0),
        end=datetime(2025, 1, 18, 0, 0),
    )
    result = searcher.check_component(cal)
    assert result, "Multi-day all-day event should match range overlapping it"


def test_all_day_event_no_range_filter() -> None:
    """All-day event should match when no date range is specified."""
    cal = Calendar()
    event = Event()
    event.add("uid", "allday")
    event.add("summary", "Holiday")
    event.add("dtstart", date(2025, 12, 25))
    cal.add_component(event)

    searcher = Searcher(event=True)
    result = searcher.check_component(cal)
    assert result, "All-day event should match when no date filter specified"


def test_all_day_event_no_end_defaults_one_day() -> None:
    """All-day event with no DTEND should default to one-day duration."""
    cal = Calendar()
    event = Event()
    event.add("uid", "single-day")
    event.add("summary", "One Day Event")
    event.add("dtstart", date(2025, 1, 15))
    # No DTEND - should default to one day
    cal.add_component(event)

    # Search for the same day
    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 16, 0, 0),
    )
    assert searcher.check_component(cal), (
        "Event with date-only start and no end should match that day"
    )


def test_all_day_event_no_end_not_match_next_day() -> None:
    """All-day event with no DTEND should not extend to next day."""
    cal = Calendar()
    event = Event()
    event.add("uid", "single-day")
    event.add("summary", "One Day Event")
    event.add("dtstart", date(2025, 1, 15))
    # No DTEND - should default to one day
    cal.add_component(event)

    # Search for next day only
    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 16, 0, 0),
        end=datetime(2025, 1, 17, 0, 0),
    )
    assert not searcher.check_component(cal), (
        "Event with one-day duration should not match next day"
    )


def test_event_with_duration_no_end() -> None:
    """Event with DURATION set but no DTEND should work correctly."""
    from datetime import timedelta

    cal = Calendar()
    event = Event()
    event.add("uid", "duration-event")
    event.add("summary", "Event with Duration")
    event.add("dtstart", datetime(2025, 1, 15, 10, 0))
    event.add("duration", timedelta(hours=2))  # 2-hour duration
    # No DTEND - should use DURATION
    cal.add_component(event)

    # Search for time range covering the event
    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 15, 9, 0),
        end=datetime(2025, 1, 15, 13, 0),
    )
    assert searcher.check_component(cal), "Event with DURATION should match"


def test_event_with_duration_date_start() -> None:
    """All-day event with DURATION set should work correctly."""
    from datetime import timedelta

    cal = Calendar()
    event = Event()
    event.add("uid", "multiday-duration")
    event.add("summary", "Multi-day Event")
    event.add("dtstart", date(2025, 1, 15))
    event.add("duration", timedelta(days=3))  # 3-day duration
    cal.add_component(event)

    # Search for second day of the event
    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 16, 0, 0),
        end=datetime(2025, 1, 17, 0, 0),
    )
    assert searcher.check_component(cal), "Multi-day event with DURATION should match middle day"


def test_todo_with_duration_no_due() -> None:
    """Todo with DURATION but no DUE should work correctly."""
    from datetime import timedelta

    task = Todo()
    task.add("uid", "task-duration")
    task.add("summary", "Task with Duration")
    task.add("dtstart", datetime(2025, 1, 15, 10, 0))
    task.add("duration", timedelta(hours=4))
    # No DUE - should use DURATION
    cal = Calendar()
    cal.add_component(task)

    searcher = Searcher(
        todo=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 16, 0, 0),
    )
    assert searcher.check_component(cal), "Todo with DURATION should match"


def test_todo_no_dtstart_no_due_with_created_completed() -> None:
    """Todo with only CREATED and COMPLETED (no DTSTART/DUE) should be handled."""
    task = Todo()
    task.add("uid", "task-created-completed")
    task.add("summary", "Completed Task")
    task.add("created", datetime(2025, 1, 10, 10, 0))
    task.add("completed", datetime(2025, 1, 15, 14, 0))
    # No DTSTART or DUE
    cal = Calendar()
    cal.add_component(task)

    # According to RFC4791 9.9, tasks without DTSTART or DUE match any time range
    searcher = Searcher(
        todo=True,
        include_completed=True,
        start=datetime(2025, 1, 14, 0, 0),
        end=datetime(2025, 1, 16, 0, 0),
    )
    result = searcher.check_component(cal)
    assert result, "Todo without DTSTART/DUE should match time range (RFC4791 9.9)"


def test_todo_no_dtstart_no_due_created_only() -> None:
    """Todo with only CREATED (no DTSTART/DUE/COMPLETED) should be handled."""
    task = Todo()
    task.add("uid", "task-created-only")
    task.add("summary", "Task with only CREATED")
    task.add("created", datetime(2025, 1, 10, 10, 0))
    # No DTSTART, DUE, or COMPLETED
    cal = Calendar()
    cal.add_component(task)

    # Should match any time range per RFC4791 9.9
    searcher = Searcher(
        todo=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 20, 0, 0),
    )
    result = searcher.check_component(cal)
    assert result, "Todo without DTSTART/DUE should match any time range"


def test_todo_no_dtstart_no_due_no_timestamps() -> None:
    """Todo with no time-related fields at all should match any range."""
    task = Todo()
    task.add("uid", "minimal-task")
    task.add("summary", "Minimal Task")
    # No DTSTART, DUE, CREATED, or COMPLETED
    cal = Calendar()
    cal.add_component(task)

    searcher = Searcher(
        todo=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 12, 31, 23, 59),
    )
    result = searcher.check_component(cal)
    assert result, "Todo with no time fields should match any time range"


def test_event_duration_extends_beyond_range() -> None:
    """Event with DURATION extending beyond search range should still match."""
    from datetime import timedelta

    cal = Calendar()
    event = Event()
    event.add("uid", "long-event")
    event.add("summary", "Long Event")
    event.add("dtstart", datetime(2025, 1, 10, 10, 0))
    event.add("duration", timedelta(days=10))  # Ends Jan 20
    cal.add_component(event)

    # Search for middle portion (Jan 14-16)
    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 14, 0, 0),
        end=datetime(2025, 1, 16, 0, 0),
    )
    assert searcher.check_component(cal), "Event with DURATION should match partial overlap"


def test_all_day_event_duration_boundary() -> None:
    """All-day event with DURATION at range boundary should match correctly."""
    from datetime import timedelta

    cal = Calendar()
    event = Event()
    event.add("uid", "boundary-event")
    event.add("summary", "Boundary Event")
    event.add("dtstart", date(2025, 1, 15))
    event.add("duration", timedelta(days=2))  # Jan 15-16
    cal.add_component(event)

    # Search exactly matching the duration
    searcher = Searcher(
        event=True,
        start=datetime(2025, 1, 15, 0, 0),
        end=datetime(2025, 1, 17, 0, 0),
    )
    assert searcher.check_component(cal), "Event duration should match range exactly"
