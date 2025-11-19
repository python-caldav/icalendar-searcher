"""Test recurring todos with completed and cancelled exception occurrences.

This tests that when expand=True and todo=True (with implicit include_completed=False),
the completed and cancelled exception occurrences are filtered out.
"""

from datetime import datetime

from icalendar import Calendar, Todo
from icalendar.prop import vRecur

from icalendar_searcher import Searcher


def test_recurring_todo_with_completed_cancelled_exceptions() -> None:
    """Recurring todo with completed/cancelled exceptions should filter them out.

    When searching for todos with expand=True and include_completed=False (implicit
    when todo=True), the expanded occurrences that are completed or cancelled should
    not be returned, even if they are explicitly defined as exception occurrences.
    """
    cal = Calendar()

    # Create a recurring todo (master/base event)
    todo_base = Todo()
    todo_base.add("uid", "weekly-task")
    todo_base.add("summary", "Weekly Review")
    todo_base.add("dtstart", datetime(2025, 1, 6, 10, 0))  # Monday
    todo_base.add("due", datetime(2025, 1, 6, 17, 0))
    todo_base.add("status", "NEEDS-ACTION")
    todo_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=10))  # 10 weekly occurrences
    cal.add_component(todo_base)

    # Exception 1: Second occurrence (Jan 13) - COMPLETED
    todo_exception1 = Todo()
    todo_exception1.add("uid", "weekly-task")
    todo_exception1.add("summary", "Weekly Review")
    todo_exception1.add("dtstart", datetime(2025, 1, 13, 10, 0))
    todo_exception1.add("due", datetime(2025, 1, 13, 17, 0))
    todo_exception1.add("recurrence-id", datetime(2025, 1, 13, 10, 0))
    todo_exception1.add("status", "COMPLETED")
    todo_exception1.add("completed", datetime(2025, 1, 13, 16, 30))
    cal.add_component(todo_exception1)

    # Exception 2: Third occurrence (Jan 20) - CANCELLED
    todo_exception2 = Todo()
    todo_exception2.add("uid", "weekly-task")
    todo_exception2.add("summary", "Weekly Review - Cancelled due to holiday")
    todo_exception2.add("dtstart", datetime(2025, 1, 20, 10, 0))
    todo_exception2.add("due", datetime(2025, 1, 20, 17, 0))
    todo_exception2.add("recurrence-id", datetime(2025, 1, 20, 10, 0))
    todo_exception2.add("status", "CANCELLED")
    cal.add_component(todo_exception2)

    # Exception 3: Fourth occurrence (Jan 27) - IN-PROCESS (should be included)
    todo_exception3 = Todo()
    todo_exception3.add("uid", "weekly-task")
    todo_exception3.add("summary", "Weekly Review - In Progress")
    todo_exception3.add("dtstart", datetime(2025, 1, 27, 10, 0))
    todo_exception3.add("due", datetime(2025, 1, 27, 17, 0))
    todo_exception3.add("recurrence-id", datetime(2025, 1, 27, 10, 0))
    todo_exception3.add("status", "IN-PROCESS")
    cal.add_component(todo_exception3)

    # Create searcher with expand=True, todo=True
    # include_completed should implicitly be False when todo=True
    searcher = Searcher(
        todo=True,
        expand=True,
        start=datetime(2025, 1, 1, 0, 0),
        end=datetime(2025, 3, 10, 23, 59),  # Covers all 10 occurrences
    )

    result = searcher.check_component(cal)
    assert result, "Should return expanded todo occurrences"

    # Convert to list to examine
    occurrences = list(result)

    # Should have 10 total occurrences minus 2 (completed and cancelled) = 8
    assert len(occurrences) == 8, (
        f"Expected 8 occurrences (10 total - 1 completed - 1 cancelled), got {len(occurrences)}"
    )

    # Verify none of the returned occurrences are completed or cancelled
    for i, occurrence in enumerate(occurrences, 1):
        status = occurrence.get("STATUS")
        assert status not in ("COMPLETED", "CANCELLED"), (
            f"Occurrence {i} has status {status} but should not be returned "
            f"when include_completed=False"
        )

    # Verify the IN-PROCESS exception is included
    in_process_occurrences = [occ for occ in occurrences if occ.get("STATUS") == "IN-PROCESS"]
    assert len(in_process_occurrences) == 1, "Should have exactly one IN-PROCESS occurrence"
    assert in_process_occurrences[0]["SUMMARY"] == "Weekly Review - In Progress"

    # Verify NEEDS-ACTION occurrences are included (from base event)
    needs_action_occurrences = [occ for occ in occurrences if occ.get("STATUS") == "NEEDS-ACTION"]
    assert len(needs_action_occurrences) == 7, (
        f"Should have 7 NEEDS-ACTION occurrences (1st, 5th-10th), "
        f"got {len(needs_action_occurrences)}"
    )


def test_recurring_todo_with_completed_exceptions_include_completed_true() -> None:
    """When include_completed=True explicitly, completed exceptions should be returned."""
    cal = Calendar()

    # Create a recurring todo
    todo_base = Todo()
    todo_base.add("uid", "daily-task")
    todo_base.add("summary", "Daily Task")
    todo_base.add("dtstart", datetime(2025, 2, 1, 9, 0))
    todo_base.add("due", datetime(2025, 2, 1, 10, 0))
    todo_base.add("status", "NEEDS-ACTION")
    todo_base.add("rrule", vRecur(FREQ="DAILY", COUNT=5))
    cal.add_component(todo_base)

    # Second occurrence - COMPLETED
    todo_exception1 = Todo()
    todo_exception1.add("uid", "daily-task")
    todo_exception1.add("summary", "Daily Task")
    todo_exception1.add("dtstart", datetime(2025, 2, 2, 9, 0))
    todo_exception1.add("due", datetime(2025, 2, 2, 10, 0))
    todo_exception1.add("recurrence-id", datetime(2025, 2, 2, 9, 0))
    todo_exception1.add("status", "COMPLETED")
    todo_exception1.add("completed", datetime(2025, 2, 2, 9, 45))
    cal.add_component(todo_exception1)

    # Third occurrence - CANCELLED
    todo_exception2 = Todo()
    todo_exception2.add("uid", "daily-task")
    todo_exception2.add("summary", "Daily Task")
    todo_exception2.add("dtstart", datetime(2025, 2, 3, 9, 0))
    todo_exception2.add("due", datetime(2025, 2, 3, 10, 0))
    todo_exception2.add("recurrence-id", datetime(2025, 2, 3, 9, 0))
    todo_exception2.add("status", "CANCELLED")
    cal.add_component(todo_exception2)

    # Create searcher with include_completed=True explicitly
    searcher = Searcher(
        todo=True,
        expand=True,
        include_completed=True,
        start=datetime(2025, 2, 1, 0, 0),
        end=datetime(2025, 2, 6, 0, 0),
    )

    result = searcher.check_component(cal)
    assert result, "Should return expanded todo occurrences"

    occurrences = list(result)

    # Should have all 5 occurrences
    assert len(occurrences) == 5, (
        f"Expected 5 occurrences when include_completed=True, got {len(occurrences)}"
    )

    # Verify we have completed and cancelled occurrences
    completed_count = sum(1 for occ in occurrences if occ.get("STATUS") == "COMPLETED")
    cancelled_count = sum(1 for occ in occurrences if occ.get("STATUS") == "CANCELLED")

    assert completed_count == 1, f"Expected 1 completed occurrence, got {completed_count}"
    assert cancelled_count == 1, f"Expected 1 cancelled occurrence, got {cancelled_count}"


def test_recurring_todo_all_exceptions_completed_returns_empty() -> None:
    """When all occurrences in range are completed/cancelled, should return empty."""
    cal = Calendar()

    # Create a recurring todo with only 3 occurrences
    todo_base = Todo()
    todo_base.add("uid", "short-task")
    todo_base.add("summary", "Short Task")
    todo_base.add("dtstart", datetime(2025, 3, 1, 14, 0))
    todo_base.add("due", datetime(2025, 3, 1, 15, 0))
    todo_base.add("status", "NEEDS-ACTION")
    todo_base.add("rrule", vRecur(FREQ="DAILY", COUNT=3))
    cal.add_component(todo_base)

    # All three occurrences as exceptions - all completed
    for day in range(1, 4):
        todo_exception = Todo()
        todo_exception.add("uid", "short-task")
        todo_exception.add("summary", "Short Task")
        dtstart = datetime(2025, 3, day, 14, 0)
        todo_exception.add("dtstart", dtstart)
        todo_exception.add("due", datetime(2025, 3, day, 15, 0))
        todo_exception.add("recurrence-id", dtstart)
        todo_exception.add("status", "COMPLETED")
        todo_exception.add("completed", datetime(2025, 3, day, 14, 30))
        cal.add_component(todo_exception)

    # Create searcher with include_completed=False (implicit)
    searcher = Searcher(
        todo=True,
        expand=True,
        start=datetime(2025, 3, 1, 0, 0),
        end=datetime(2025, 3, 4, 0, 0),
    )

    result = searcher.check_component(cal)

    # Should return False or empty list when all are completed
    if result:
        occurrences = list(result)
        assert len(occurrences) == 0, (
            f"Expected 0 occurrences when all are completed, got {len(occurrences)}"
        )
    else:
        assert not result, "Should return False when all occurrences are completed"


def test_recurring_todo_mixed_status_without_exceptions() -> None:
    """Recurring todo without exceptions should return all occurrences from base event."""
    cal = Calendar()

    # Create a recurring todo with no exceptions
    todo_base = Todo()
    todo_base.add("uid", "simple-recurring-task")
    todo_base.add("summary", "Simple Recurring Task")
    todo_base.add("dtstart", datetime(2025, 4, 1, 10, 0))
    todo_base.add("due", datetime(2025, 4, 1, 11, 0))
    todo_base.add("status", "NEEDS-ACTION")
    todo_base.add("rrule", vRecur(FREQ="WEEKLY", COUNT=4))
    cal.add_component(todo_base)

    # Create searcher
    searcher = Searcher(
        todo=True,
        expand=True,
        start=datetime(2025, 4, 1, 0, 0),
        end=datetime(2025, 5, 1, 0, 0),
    )

    result = searcher.check_component(cal)
    assert result, "Should return expanded todo occurrences"

    occurrences = list(result)

    # Should have all 4 occurrences
    assert len(occurrences) == 4, f"Expected 4 occurrences, got {len(occurrences)}"

    # All should have NEEDS-ACTION status
    for i, occurrence in enumerate(occurrences, 1):
        assert occurrence.get("STATUS") == "NEEDS-ACTION", (
            f"Occurrence {i} should have NEEDS-ACTION status"
        )
        assert occurrence["SUMMARY"] == "Simple Recurring Task"
