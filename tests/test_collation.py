"""Tests for text collation features."""

import pytest
from icalendar import Event, Todo

from icalendar_searcher import Collation, Searcher


def test_case_sensitive_search_default() -> None:
    """By default, searches should be case-sensitive (binary collation)."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Training Session")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "train", operator="contains")

    result = searcher.check_component(event)
    assert not result, "Case-sensitive search should not match 'train' in 'Training Session'"


def test_case_insensitive_search_simple_api() -> None:
    """Using case_sensitive=False should enable case-insensitive search."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Training Session")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "train", operator="contains", case_sensitive=False)

    result = searcher.check_component(event)
    assert result, "Case-insensitive search should match 'train' in 'Training Session'"


def test_case_insensitive_search_uppercase() -> None:
    """Case-insensitive search should work with uppercase filter."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "meeting with team")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "MEETING", operator="contains", case_sensitive=False)

    result = searcher.check_component(event)
    assert result, "Case-insensitive search should match 'MEETING' in 'meeting with team'"


def test_case_sensitive_search_explicit() -> None:
    """Explicitly setting case_sensitive=True should enforce case sensitivity."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Important Meeting")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "meeting", operator="contains", case_sensitive=True)

    result = searcher.check_component(event)
    assert not result, "Case-sensitive search should not match 'meeting' in 'Important Meeting'"


def test_case_insensitive_search_location() -> None:
    """Case-insensitive search should work for LOCATION property."""
    event = Event()
    event.add("uid", "123")
    event.add("location", "Conference Room A")

    searcher = Searcher(event=True)
    searcher.add_property_filter("LOCATION", "room", operator="contains", case_sensitive=False)

    result = searcher.check_component(event)
    assert result, "Case-insensitive search should match 'room' in 'Conference Room A'"


def test_case_insensitive_search_description() -> None:
    """Case-insensitive search should work for DESCRIPTION property."""
    event = Event()
    event.add("uid", "123")
    event.add("description", "Discuss PROJECT status")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "DESCRIPTION", "project", operator="contains", case_sensitive=False
    )

    result = searcher.check_component(event)
    assert result, "Case-insensitive search should match 'project' in 'Discuss PROJECT status'"


def test_multiple_filters_mixed_case_sensitivity() -> None:
    """Multiple filters can have different case sensitivity settings."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Team TRAINING")
    event.add("location", "Room 101")

    searcher = Searcher(event=True)
    # Case-insensitive filter on SUMMARY
    searcher.add_property_filter("SUMMARY", "training", operator="contains", case_sensitive=False)
    # Case-sensitive filter on LOCATION (default)
    searcher.add_property_filter("LOCATION", "Room", operator="contains")

    result = searcher.check_component(event)
    assert result, "Mixed case sensitivity filters should all match"


def test_case_sensitive_categories() -> None:
    """Category searches should be case-sensitive by default."""
    event = Event()
    event.add("uid", "123")
    event.add("categories", ["Work", "Important"])

    searcher = Searcher(event=True)
    searcher.add_property_filter("CATEGORIES", "work", operator="contains")

    result = searcher.check_component(event)
    assert not result, "Case-sensitive category search should not match 'work' in 'Work'"


def test_case_insensitive_categories() -> None:
    """Category searches can be made case-insensitive."""
    event = Event()
    event.add("uid", "123")
    event.add("categories", ["Work", "Important"])

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "CATEGORIES", "work", operator="contains", case_sensitive=False
    )

    result = searcher.check_component(event)
    assert result, "Case-insensitive category search should match 'work' in 'Work'"


def test_collation_power_user_api_binary() -> None:
    """Power users can explicitly specify BINARY collation."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Meeting")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "SUMMARY", "meeting", operator="contains", collation=Collation.BINARY
    )

    result = searcher.check_component(event)
    assert not result, "BINARY collation should be case-sensitive"


def test_collation_power_user_api_case_insensitive() -> None:
    """Power users can explicitly specify CASE_INSENSITIVE collation."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Meeting")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "SUMMARY", "meeting", operator="contains", collation=Collation.CASE_INSENSITIVE
    )

    result = searcher.check_component(event)
    assert result, "CASE_INSENSITIVE collation should match regardless of case"


def test_collation_overrides_case_sensitive() -> None:
    """Explicit collation parameter overrides case_sensitive parameter."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Meeting")

    searcher = Searcher(event=True)
    # collation=BINARY should override case_sensitive=False
    searcher.add_property_filter(
        "SUMMARY",
        "meeting",
        operator="contains",
        case_sensitive=False,
        collation=Collation.BINARY,
    )

    result = searcher.check_component(event)
    assert not result, "Explicit collation should override case_sensitive parameter"


def test_case_insensitive_sorting_simple_api() -> None:
    """Sorting should support case_sensitive parameter."""
    cal1 = Event()
    cal1.add("uid", "1")
    cal1.add("summary", "Zebra")

    cal2 = Event()
    cal2.add("uid", "2")
    cal2.add("summary", "apple")

    cal3 = Event()
    cal3.add("uid", "3")
    cal3.add("summary", "Banana")

    searcher = Searcher(event=True)
    searcher.add_sort_key("SUMMARY", case_sensitive=False)

    # Get sorting values
    val1 = searcher.sorting_value(cal1)
    val2 = searcher.sorting_value(cal2)
    val3 = searcher.sorting_value(cal3)

    # Case-insensitive sort should order: apple, Banana, Zebra
    assert val2 < val3 < val1, "Case-insensitive sorting should ignore case"


def test_case_sensitive_sorting_default() -> None:
    """By default, sorting should be case-sensitive."""
    cal1 = Event()
    cal1.add("uid", "1")
    cal1.add("summary", "Zebra")

    cal2 = Event()
    cal2.add("uid", "2")
    cal2.add("summary", "apple")

    searcher = Searcher(event=True)
    searcher.add_sort_key("SUMMARY")  # Default: case-sensitive

    val1 = searcher.sorting_value(cal1)
    val2 = searcher.sorting_value(cal2)

    # Case-sensitive sort: uppercase comes before lowercase in ASCII
    assert val1 < val2, "Case-sensitive sorting should sort 'Zebra' before 'apple'"


def test_collation_with_todo() -> None:
    """Collation should work with VTODO components."""
    task = Todo()
    task.add("uid", "123")
    task.add("summary", "FIX the bug")

    searcher = Searcher(todo=True)
    searcher.add_property_filter("SUMMARY", "fix", operator="contains", case_sensitive=False)

    result = searcher.check_component(task)
    assert result, "Case-insensitive search should work with VTODO"


def test_pyicu_not_available_unicode_collation() -> None:
    """UNICODE collation should raise error if PyICU not installed."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Test")

    searcher = Searcher(event=True)

    # Try to use UNICODE collation (will fail if PyICU not installed)
    try:
        searcher.add_property_filter(
            "SUMMARY", "test", operator="contains", collation=Collation.UNICODE
        )
        result = searcher.check_component(event)
        # If PyICU is installed, this should work
        # If not installed, CollationError should be raised
    except Exception as e:
        # Should get CollationError if PyICU not installed
        assert "PyICU" in str(e), "Error message should mention PyICU requirement"


def test_pyicu_not_available_locale_collation() -> None:
    """LOCALE collation should raise error if PyICU not installed."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Test")

    searcher = Searcher(event=True)

    # Try to use LOCALE collation (will fail if PyICU not installed)
    try:
        searcher.add_property_filter(
            "SUMMARY", "test", operator="contains", collation=Collation.LOCALE, locale="en_US"
        )
        result = searcher.check_component(event)
        # If PyICU is installed, this should work
        # If not installed, CollationError should be raised
    except Exception as e:
        # Should get CollationError if PyICU not installed
        assert "PyICU" in str(e), "Error message should mention PyICU requirement"


def test_backwards_compatibility_old_test() -> None:
    """The old case-insensitive test should now fail with new default."""
    # This is the old test from test_property_filtering.py
    event = Event()
    event.add("uid", "123")
    event.add("summary", "TRAINING SESSION")

    searcher = Searcher(event=True)
    searcher.add_property_filter("SUMMARY", "train", operator="contains")

    result = searcher.check_component(event)
    # With the new default (case-sensitive), this should NOT match
    assert not result, "Default behavior is now case-sensitive"

    # But with case_sensitive=False, it should match
    searcher2 = Searcher(event=True)
    searcher2.add_property_filter("SUMMARY", "train", operator="contains", case_sensitive=False)
    result2 = searcher2.check_component(event)
    assert result2, "Case-insensitive mode should match"
