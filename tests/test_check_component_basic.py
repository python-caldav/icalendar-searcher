"""
Automated tests for basic check_component functionality.
These tests help identify where the logic is failing.
"""

from datetime import datetime

from icalendar import Calendar, Event, Todo

from icalendar_searcher import Searcher


def test_basic_todo_no_filters() -> None:
    """A basic todo with no filters should match."""
    task = Todo()
    task.add("uid", "123")

    searcher = Searcher(todo=True)
    result = searcher.check_component(task)
    assert result, "Basic todo should match when todo=True"


def test_basic_event_no_filters() -> None:
    """A basic event with no filters should match."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    cal.add_component(event)

    searcher = Searcher()
    result = searcher.check_component(cal)
    assert result, "Basic event should match with no filters"


def test_event_with_event_filter_true() -> None:
    """An event should match when event=True."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    cal.add_component(event)

    searcher = Searcher(event=True)
    result = searcher.check_component(cal)
    assert result, "Event should match when event=True"


def test_event_with_todo_filter_should_not_match() -> None:
    """An event should NOT match when todo=True."""
    cal = Calendar()
    event = Event()
    event.add("uid", "event123")
    cal.add_component(event)

    searcher = Searcher(todo=True)
    result = searcher.check_component(cal)
    assert not result, "Event should not match when todo=True"


def test_todo_with_needs_action_status() -> None:
    """A todo with STATUS=NEEDS-ACTION should match."""
    task = Todo()
    task.add("status", "NEEDS-ACTION")
    task.add("uid", "123")

    searcher = Searcher(todo=True)
    result = searcher.check_component(task)
    assert result, "Todo with STATUS=NEEDS-ACTION should match"


def test_completed_todo_with_include_completed_true() -> None:
    """A completed todo should match when include_completed=True."""
    task = Todo()
    task.add("completed", datetime(2000, 1, 2))
    task.add("uid", "123")

    searcher = Searcher(todo=True, include_completed=True)
    result = searcher.check_component(task)
    assert result, "Completed todo should match when include_completed=True"


def test_completed_todo_with_include_completed_false() -> None:
    """A completed todo should NOT match when include_completed=False."""
    task = Todo()
    task.add("completed", datetime(2000, 1, 2))
    task.add("uid", "123")

    searcher = Searcher(todo=True, include_completed=False)
    result = searcher.check_component(task)
    assert not result, "Completed todo should not match when include_completed=False"


def test_cancelled_todo_should_not_match() -> None:
    """A cancelled todo should NOT match when todo=True (default include_completed)."""
    task = Todo()
    task.add("status", "CANCELLED")
    task.add("uid", "123")

    searcher = Searcher(todo=True)
    result = searcher.check_component(task)
    assert not result, "Cancelled todo should not match when todo=True"


def test_cancelled_todo_with_include_completed_true() -> None:
    """A cancelled todo should match when include_completed=True."""
    task = Todo()
    task.add("status", "CANCELLED")
    task.add("uid", "123")

    searcher = Searcher(todo=True, include_completed=True)
    result = searcher.check_component(task)
    assert result, "Cancelled todo should match when include_completed=True"


def test_todo_no_status_no_completed() -> None:
    """A todo with no status and no completed field should match."""
    task = Todo()
    task.add("uid", "123")

    searcher = Searcher(todo=True)
    result = searcher.check_component(task)
    assert result, "Todo with no status should match (defaults to NEEDS-ACTION)"


def test_todo_no_status_with_completed() -> None:
    """A todo with no status but COMPLETED field should not match by default."""
    task = Todo()
    task.add("completed", datetime(2000, 1, 2))
    task.add("uid", "123")

    searcher = Searcher(todo=True)
    result = searcher.check_component(task)
    assert not result, (
        "Todo with COMPLETED should not match when include_completed defaults to False"
    )
