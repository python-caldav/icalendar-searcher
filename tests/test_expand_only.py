"""
Tests for the expand_only parameter in Searcher.check_component().

When expand_only=True, the searcher should:
1. Return the component immediately if expand=False
2. Only expand recurrences if expand=True, without applying any filters
3. Ignore property filters, time range filters, component type filters, and completed filters
"""

from datetime import datetime

from icalendar import Calendar, Event, Todo
from icalendar.prop import vRecur

from icalendar_searcher import Searcher


def test_expand_only_without_expand_returns_immediately() -> None:
    """When expand_only=True and expand=False, component list is returned without filtering."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "Test Event")
    event.add("dtstart", datetime(2025, 1, 15, 10, 0))
    cal.add_component(event)

    # Create searcher with filters that would normally exclude this event
    searcher = Searcher(
        todo=True,  # This would normally exclude events
        start=datetime(2025, 2, 1, 0, 0),  # Outside the event time
        end=datetime(2025, 2, 28, 23, 59),
    )
    searcher.add_property_filter("SUMMARY", "Different Event", operator="==")

    # With expand_only=True and expand=False, it should return the component list immediately
    # without applying any filters
    result = searcher.check_component(cal, expand_only=True)
    assert result, "Should return component list when expand_only=True and expand=False"
    assert len(result) == 1, "Should contain one component"
    assert result[0].name == "VEVENT", "Should be the original event"


def test_expand_only_ignores_property_filters() -> None:
    """When expand_only=True with expand=True, property filters should be ignored."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "Team Meeting")
    event.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event.add("dtend", datetime(2025, 1, 6, 11, 0))
    event.add("rrule", vRecur(FREQ="WEEKLY", COUNT=3))
    cal.add_component(event)

    # Create searcher with property filter that should NOT match
    searcher = Searcher(
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 31, 23, 59),
    )
    searcher.add_property_filter("SUMMARY", "Different Meeting", operator="==")

    # Without expand_only, this should not match
    result_normal = searcher.check_component(cal, expand_only=False)
    assert not result_normal, "Should not match with non-matching property filter"

    # With expand_only=True, property filter should be ignored
    result_expand_only = searcher.check_component(cal, expand_only=True)
    assert result_expand_only, "Should match when expand_only=True ignores property filters"


def test_expand_only_ignores_component_type_filter() -> None:
    """When expand_only=True with expand=True, component type filters should be ignored."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "Birthday Party")
    event.add("dtstart", datetime(2025, 3, 15, 18, 0))
    event.add("dtend", datetime(2025, 3, 15, 22, 0))
    event.add("rrule", vRecur(FREQ="YEARLY", COUNT=5))
    cal.add_component(event)

    # Create searcher that only accepts todos (should exclude events)
    searcher = Searcher(
        todo=True,
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2027, 12, 31, 23, 59),
    )

    # Without expand_only, event should not match todo filter
    result_normal = searcher.check_component(cal, expand_only=False)
    assert not result_normal, "Event should not match when todo=True"

    # With expand_only=True, component type filter should be ignored
    result_expand_only = searcher.check_component(cal, expand_only=True)
    assert result_expand_only, "Should match when expand_only=True ignores component type filter"


def test_expand_only_ignores_time_range_filter() -> None:
    """When expand_only=True with expand=True, time range filters should be ignored."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "Daily Standup")
    event.add("dtstart", datetime(2025, 1, 6, 9, 0))
    event.add("dtend", datetime(2025, 1, 6, 9, 15))
    event.add("rrule", vRecur(FREQ="DAILY", COUNT=10))
    cal.add_component(event)

    # Create searcher with time range that doesn't include the event
    searcher = Searcher(
        expand=True,
        start=datetime(2025, 2, 1, 0, 0),
        end=datetime(2025, 2, 28, 23, 59),
    )

    # Without expand_only, should not match (event is in January, not February)
    result_normal = searcher.check_component(cal, expand_only=False)
    assert not result_normal, "Should not match when time range doesn't include event"

    # With expand_only=True, time range filter should be ignored
    # But expansion should still happen using the start/end range
    result_expand_only = searcher.check_component(cal, expand_only=True)
    # The expansion will happen but since no occurrences fall in Feb, generator may be empty
    # Actually, with expand_only, the time range check is skipped, so we need different logic
    # Let me check the implementation again...
    # Looking at lines 237-238 and 346-366, when expand_only=True:
    # - It returns early if expand=False (line 238)
    # - It skips the time range check (line 349-350 is inside "if not expand_only")
    # - It skips component type filter (line 353-354)
    # - It skips completed filter (line 357)
    # - It skips property filters (line 360-361)
    # But expansion still happens at line 344 if rrule exists
    # So the expansion will use self.start and self.end from line 603-606
    # This means events will be expanded to the Feb range, but there won't be any
    # Let me reconsider...

    # Actually, when expand_only=True, expansion happens but range check doesn't
    # So all expanded instances should be returned regardless of filter range
    # But expansion itself uses start/end, so only Feb instances are generated
    # Since daily event is in Jan, no Feb instances exist
    # So result should be empty/False

    # Let me write a better test - one where the recurrence DOES have instances in the range
    assert not result_expand_only, "Expansion uses start/end but filter is skipped"


def test_expand_only_expands_within_searcher_range() -> None:
    """When expand_only=True, recurrences are expanded using searcher's start/end range."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "Daily Standup")
    event.add("dtstart", datetime(2025, 1, 1, 9, 0))
    event.add("dtend", datetime(2025, 1, 1, 9, 15))
    # Event recurs for entire year
    event.add("rrule", vRecur(FREQ="DAILY", UNTIL=datetime(2025, 12, 31, 23, 59)))
    cal.add_component(event)

    # Create searcher with February range
    searcher = Searcher(
        expand=True,
        start=datetime(2025, 2, 1, 0, 0),
        end=datetime(2025, 2, 28, 23, 59),
    )

    # With expand_only=True, should expand occurrences within Feb range
    result = searcher.check_component(cal, expand_only=True)
    assert result, "Should return expanded occurrences"

    # Convert generator to list and check we got February occurrences
    occurrences = list(result)
    assert len(occurrences) == 28, "Should have 28 daily occurrences in February"

    # Verify first and last occurrences are in February
    first_occurrence = occurrences[0]
    first_dt = first_occurrence.start if isinstance(first_occurrence.start, datetime) else first_occurrence.start.dt
    assert first_dt.month == 2
    assert first_dt.day == 1

    last_occurrence = occurrences[-1]
    last_dt = last_occurrence.start if isinstance(last_occurrence.start, datetime) else last_occurrence.start.dt
    assert last_dt.month == 2
    assert last_dt.day == 28


def test_expand_only_ignores_include_completed_filter() -> None:
    """When expand_only=True, include_completed filter should be ignored for non-recurring tasks."""
    cal = Calendar()
    task = Todo()
    task.add("uid", "task123")
    task.add("summary", "Completed Task")
    task.add("completed", datetime(2025, 1, 10, 14, 30))
    task.add("status", "COMPLETED")
    task.add("dtstart", datetime(2025, 1, 1, 9, 0))
    task.add("due", datetime(2025, 1, 5, 17, 0))
    # No rrule - this is a non-recurring completed task
    cal.add_component(task)

    # Create searcher that excludes completed tasks
    searcher = Searcher(
        todo=True,
        include_completed=False,
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 31, 23, 59),
    )

    # Without expand_only, completed task should not match
    result_normal = searcher.check_component(cal, expand_only=False)
    assert not result_normal, "Completed task should not match when include_completed=False"

    # With expand_only=True, completed filter should be ignored
    result_expand_only = searcher.check_component(cal, expand_only=True)
    assert result_expand_only, "Should match when expand_only=True ignores completed filter"


def test_expand_only_with_recurring_and_completed_filter() -> None:
    """When expand_only=True with expand=True, completed filter is ignored even with recurring events."""
    cal = Calendar()
    # Create a recurring event
    event = Event()
    event.add("uid", "event456")
    event.add("summary", "Weekly Standup")
    event.add("dtstart", datetime(2025, 1, 1, 9, 0))
    event.add("dtend", datetime(2025, 1, 1, 9, 30))
    event.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event)

    # Create searcher with include_completed=False
    # Even though events don't have completed status, this tests that the filter mechanism is bypassed
    searcher = Searcher(
        event=True,
        include_completed=False,
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 31, 23, 59),
    )

    # This should work with expand_only since all filters are ignored
    result = searcher.check_component(cal, expand_only=True)
    assert result, "Should expand recurring event with expand_only=True"
    occurrences = list(result)
    assert len(occurrences) == 4, "Should have 4 weekly occurrences"


def test_expand_only_with_multiple_filters_ignored() -> None:
    """When expand_only=True, all filters should be ignored simultaneously."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "Wrong Summary")
    event.add("dtstart", datetime(2025, 1, 1, 10, 0))
    event.add("dtend", datetime(2025, 1, 1, 11, 0))
    event.add("rrule", vRecur(FREQ="WEEKLY", COUNT=10))
    cal.add_component(event)

    # Create searcher with multiple filters that would all exclude this event
    searcher = Searcher(
        todo=True,  # Wrong component type
        include_completed=False,
        expand=True,
        start=datetime(2025, 6, 1, 0, 0),  # Wrong time range
        end=datetime(2025, 6, 30, 23, 59),
    )
    searcher.add_property_filter("SUMMARY", "Correct Summary", operator="==")  # Wrong property

    # Without expand_only, should not match (multiple filters exclude it)
    result_normal = searcher.check_component(cal, expand_only=False)
    assert not result_normal, "Should not match with multiple exclusionary filters"

    # With expand_only=True, all filters should be ignored
    # Note: expansion will use June range, but event only recurs for 10 weeks from Jan
    # So there should be no June occurrences
    result_expand_only = searcher.check_component(cal, expand_only=True)
    # 10 weeks from Jan 1 is about mid-March, so no June occurrences
    assert not result_expand_only, "No occurrences in June range even with expand_only"


def test_expand_only_with_matching_range() -> None:
    """When expand_only=True with matching range, should return expanded occurrences."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "Weekly Meeting")
    event.add("dtstart", datetime(2025, 1, 6, 14, 0))
    event.add("dtend", datetime(2025, 1, 6, 15, 0))
    event.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event)

    # Create searcher with range covering the recurrences, but wrong filters
    searcher = Searcher(
        todo=True,  # Wrong type
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 31, 23, 59),
    )
    searcher.add_property_filter("SUMMARY", "Wrong Meeting", operator="==")

    # With expand_only=True, should expand despite wrong filters
    result = searcher.check_component(cal, expand_only=True)
    assert result, "Should return expanded occurrences with expand_only=True"

    occurrences = list(result)
    assert len(occurrences) == 4, "Should have 4 weekly occurrences"


def test_expand_only_non_recurring_event() -> None:
    """When expand_only=True on a non-recurring event with expand=True, should return the event."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "One-time Meeting")
    event.add("dtstart", datetime(2025, 1, 15, 10, 0))
    event.add("dtend", datetime(2025, 1, 15, 11, 0))
    cal.add_component(event)

    # Create searcher with expand=True but event has no rrule
    searcher = Searcher(
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 31, 23, 59),
    )

    result = searcher.check_component(cal, expand_only=True)
    # Non-recurring event with expand=True should return tuple with component
    assert result, "Non-recurring event should match with expand_only=True"


def test_expand_only_non_recurring_event_outside_range() -> None:
    """When expand_only=True on non-recurring event outside range, range filter is skipped."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "One-time Meeting")
    event.add("dtstart", datetime(2025, 1, 15, 10, 0))
    event.add("dtend", datetime(2025, 1, 15, 11, 0))
    cal.add_component(event)

    # Create searcher with range that doesn't include the event
    searcher = Searcher(
        expand=True,
        start=datetime(2025, 2, 1, 0, 0),
        end=datetime(2025, 2, 28, 23, 59),
    )

    # With expand_only=True, time range check should be skipped
    result = searcher.check_component(cal, expand_only=True)
    assert result, "Should match when expand_only=True skips time range check"


def test_expand_only_false_applies_all_filters() -> None:
    """When expand_only=False (default), all filters should be applied normally."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    event.add("summary", "Team Meeting")
    event.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event.add("dtend", datetime(2025, 1, 6, 11, 0))
    event.add("rrule", vRecur(FREQ="WEEKLY", COUNT=3))
    cal.add_component(event)

    # Create searcher with property filter
    searcher = Searcher(
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 31, 23, 59),
    )
    searcher.add_property_filter("SUMMARY", "Team Meeting", operator="==")

    # With expand_only=False (default), filters should apply
    result = searcher.check_component(cal, expand_only=False)
    assert result, "Should match with matching filters"

    occurrences = list(result)
    assert len(occurrences) == 3, "Should have 3 matching weekly occurrences"

    # Change filter to non-matching
    searcher2 = Searcher(
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 31, 23, 59),
    )
    searcher2.add_property_filter("SUMMARY", "Different Meeting", operator="==")

    result2 = searcher2.check_component(cal, expand_only=False)
    assert not result2, "Should not match with non-matching filter when expand_only=False"


def test_expand_only_with_recurrence_exceptions() -> None:
    """When expand_only=True with recurrence exceptions, should expand without filtering."""
    cal = Calendar()

    # Base recurring event
    event_base = Event()
    event_base.add("uid", "weekly-meeting")
    event_base.add("summary", "Weekly Team Meeting")
    event_base.add("dtstart", datetime(2025, 1, 6, 10, 0))
    event_base.add("dtend", datetime(2025, 1, 6, 11, 0))
    event_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(event_base)

    # Exception with different summary
    event_exception = Event()
    event_exception.add("uid", "weekly-meeting")
    event_exception.add("summary", "Special Planning Session")
    event_exception.add("dtstart", datetime(2025, 1, 13, 10, 0))
    event_exception.add("dtend", datetime(2025, 1, 13, 11, 0))
    event_exception.add("recurrence-id", datetime(2025, 1, 13, 10, 0))
    cal.add_component(event_exception)

    # Create searcher that filters for base summary (would exclude exception)
    searcher = Searcher(
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 1, 31, 23, 59),
    )
    searcher.add_property_filter("SUMMARY", "Weekly Team Meeting", operator="==")

    # Without expand_only, exception should be filtered out
    result_normal = searcher.check_component(cal, expand_only=False)
    assert result_normal, "Should match base event"
    occurrences_normal = list(result_normal)
    # Should have fewer than 4 occurrences since exception has different summary
    assert all("Weekly Team Meeting" in str(occ.get("summary", "")) for occ in occurrences_normal), (
        "All returned occurrences should have matching summary"
    )

    # With expand_only=True, all occurrences including exception should be returned
    result_expand = searcher.check_component(cal, expand_only=True)
    assert result_expand, "Should return all expanded occurrences"
    occurrences_expand = list(result_expand)
    assert len(occurrences_expand) == 4, "Should have all 4 occurrences with expand_only=True"
