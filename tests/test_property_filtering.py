"""
Automated tests for property filtering functionality.
Tests the _check_property_filters method and property filtering in check_component.
"""

from icalendar import Event, Todo

from icalendar_searcher import Searcher


def test_property_filter_contains_match() -> None:
    """Property filter with 'contains' operator should match substring."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Training session")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "rain", operator="contains")

    result = searcher.check_component(event)
    assert result, "Event with 'Training session' should match 'contains' 'rain'"


def test_property_filter_contains_no_match() -> None:
    """Property filter with 'contains' operator should not match if substring not found."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Meeting with team")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "rain", operator="contains")

    result = searcher.check_component(event)
    assert not result, "Event with 'Meeting with team' should not match 'contains' 'rain'"


def test_property_filter_contains_case_insensitive() -> None:
    """Property filter with 'contains' can be case-insensitive with case_sensitive=False."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "TRAINING SESSION")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "train", operator="contains", case_sensitive=False)

    result = searcher.check_component(event)
    assert result, "Contains filter with case_sensitive=False should be case-insensitive"


def test_property_filter_contains_missing_property() -> None:
    """Property filter should not match if property is missing."""
    event = Event()
    event.add("uid", "123")
    # No SUMMARY property

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "meeting", operator="contains")

    result = searcher.check_component(event)
    assert not result, "Event without SUMMARY should not match SUMMARY filter"


def test_property_filter_equals_match() -> None:
    """Property filter with '==' operator should match exact value."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Team Meeting")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "Team Meeting", operator="==")

    result = searcher.check_component(event)
    assert result, "Event should match with exact equality"

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "team meeting", operator="==", case_sensitive=False)

    result = searcher.check_component(event)
    assert result, "Event should match with case insensitive equality"

def test_property_filter_equals_no_match() -> None:
    """Property filter with '==' operator should not match different value."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Team Meeting")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "Different Meeting", operator="==")

    result = searcher.check_component(event)
    assert not result, "Event should not match with different value"


def test_property_filter_undef_property_not_defined() -> None:
    """Property filter with 'undef' should match when property is NOT defined."""
    event = Event()
    event.add("uid", "123")
    # No LOCATION property

    searcher = Searcher(event=True)
    searcher.add_property_filter("LOCATION", None, operator="undef")

    result = searcher.check_component(event)
    assert result, "Event without LOCATION should match 'undef' filter"


def test_property_filter_undef_property_is_defined() -> None:
    """Property filter with 'undef' should NOT match when property IS defined."""
    event = Event()
    event.add("uid", "123")
    event.add("location", "Conference Room A")

    searcher = Searcher(event=True)
    searcher.add_property_filter("LOCATION", None, operator="undef")

    result = searcher.check_component(event)
    assert not result, "Event with LOCATION should not match 'undef' filter"


def test_multiple_property_filters_all_match() -> None:
    """Multiple property filters should all need to match (AND logic)."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Team Training")
    event.add("location", "Room 101")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "Training", operator="contains")
    searcher.add_property_filter("LOCATION", "Room", operator="contains")

    result = searcher.check_component(event)
    assert result, "Event should match when all filters match"


def test_multiple_property_filters_one_fails() -> None:
    """If any property filter fails, the component should not match."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Team Training")
    event.add("location", "Room 101")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "train", operator="contains")
    searcher.add_property_filter("LOCATION", "Office", operator="contains")

    result = searcher.check_component(event)
    assert not result, "Event should not match when any filter fails"


def test_property_filter_on_todo() -> None:
    """Property filters should work on VTODO components."""
    task = Todo()
    task.add("uid", "123")
    task.add("summary", "Fix the bug")

    searcher = Searcher(todo=True)
    searcher.add_property_filter("SUMMARY", "bug", operator="contains")

    result = searcher.check_component(task)
    assert result, "Todo with 'Fix the bug' should match 'contains' 'bug'"


def test_property_filter_with_status() -> None:
    """Property filter should work with STATUS property."""
    task = Todo()
    task.add("uid", "123")
    task.add("status", "NEEDS-ACTION")

    searcher = Searcher(todo=True, include_completed=True)
    searcher.add_property_filter("STATUS", "NEEDS-ACTION", operator="==")

    result = searcher.check_component(task)
    assert result, "Todo with STATUS=NEEDS-ACTION should match equality filter"


def test_property_filter_combined_with_component_type() -> None:
    """Property filter should work together with component type filtering."""
    # Create a todo
    task = Todo()
    task.add("uid", "123")
    task.add("summary", "Important task")

    # Create an event
    event = Event()
    event.add("uid", "456")
    event.add("summary", "Important meeting")

    # Filter for todos with "task" in summary
    searcher = Searcher(todo=True)
    searcher.add_property_filter("SUMMARY", "task", operator="contains")

    assert searcher.check_component(task), "Todo with 'task' should match"
    assert not searcher.check_component(event), "Event should be filtered out by component type"


def test_check_property_filters_directly() -> None:
    """Test _check_property_filters method directly."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Test Event")

    searcher = Searcher()
    searcher.add_property_filter("SUMMARY", "Test", operator="contains")

    # Test the internal method directly
    assert searcher._check_property_filters(event), "Should match with 'contains' filter"


def test_check_property_filters_no_filters() -> None:
    """_check_property_filters should return True when no filters are set."""
    event = Event()
    event.add("uid", "123")

    searcher = Searcher()

    # No filters added
    assert searcher._check_property_filters(event), "Should match when no filters set"
