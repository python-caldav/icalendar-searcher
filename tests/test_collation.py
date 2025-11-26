"""Tests for text collation features."""

from unittest.mock import patch

import pytest
from icalendar import Event, Todo

from icalendar_searcher import Collation, Searcher
from icalendar_searcher.collation import HAS_PYICU, CollationError


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
    searcher.add_property_filter("CATEGORIES", "work", operator="contains", case_sensitive=False)

    result = searcher.check_component(event)
    assert result, "Case-insensitive category search should match 'work' in 'Work'"


def test_collation_power_user_api_binary() -> None:
    """Power users can explicitly specify SIMPLE collation with case_sensitive=True."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Meeting")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "SUMMARY", "meeting", operator="contains", collation=Collation.SIMPLE, case_sensitive=True
    )

    result = searcher.check_component(event)
    assert not result, "SIMPLE collation with case_sensitive=True should be case-sensitive"


def test_collation_power_user_api_case_insensitive() -> None:
    """Power users can explicitly specify SIMPLE collation with case_sensitive=False."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Meeting")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "SUMMARY", "meeting", operator="contains", collation=Collation.SIMPLE, case_sensitive=False
    )

    result = searcher.check_component(event)
    assert result, "SIMPLE collation with case_sensitive=False should match regardless of case"


def test_collation_overrides_case_sensitive() -> None:
    """case_sensitive parameter works with explicit collation."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Meeting")

    searcher = Searcher(event=True)
    # SIMPLE collation with case_sensitive=True should be case-sensitive
    searcher.add_property_filter(
        "SUMMARY",
        "meeting",
        operator="contains",
        case_sensitive=True,
        collation=Collation.SIMPLE,
    )

    result = searcher.check_component(event)
    assert not result, "SIMPLE collation with case_sensitive=True should be case-sensitive"


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


@pytest.mark.skipif(not HAS_PYICU, reason="PyICU not installed")
def test_pyicu_unicode_collation_with_pyicu() -> None:
    """UNICODE collation should work when PyICU is installed."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Test")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "SUMMARY", "test", operator="contains", collation=Collation.UNICODE
    )

    result = searcher.check_component(event)
    # With PyICU installed, case-insensitive match should work
    assert result, "UNICODE collation should match 'test' in 'Test'"


@pytest.mark.skipif(not HAS_PYICU, reason="PyICU not installed")
def test_pyicu_locale_collation_with_pyicu() -> None:
    """LOCALE collation should work when PyICU is installed."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Müller")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "SUMMARY", "müller", operator="contains", collation=Collation.LOCALE, locale="de_DE"
    )

    result = searcher.check_component(event)
    # With PyICU installed, locale-aware match should work
    assert result, "LOCALE collation should match 'müller' in 'Müller'"


@patch("icalendar_searcher.collation.HAS_PYICU", False)
def test_pyicu_not_available_unicode_collation() -> None:
    """UNICODE collation should raise CollationError if PyICU not available."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Test")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "SUMMARY", "test", operator="contains", collation=Collation.UNICODE
    )

    # Should raise CollationError when trying to use UNICODE collation
    with pytest.raises(CollationError) as exc_info:
        searcher.check_component(event)

    assert "PyICU" in str(exc_info.value), "Error should mention PyICU requirement"
    assert "icalendar-searcher[collation]" in str(exc_info.value), (
        "Error should mention installation command"
    )


@patch("icalendar_searcher.collation.HAS_PYICU", False)
def test_pyicu_not_available_locale_collation() -> None:
    """LOCALE collation should raise CollationError if PyICU not available."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Test")

    searcher = Searcher(event=True)
    searcher.add_property_filter(
        "SUMMARY", "test", operator="contains", collation=Collation.LOCALE, locale="en_US"
    )

    # Should raise CollationError when trying to use LOCALE collation
    with pytest.raises(CollationError) as exc_info:
        searcher.check_component(event)

    assert "PyICU" in str(exc_info.value), "Error should mention PyICU requirement"


@patch("icalendar_searcher.collation.HAS_PYICU", False)
def test_pyicu_not_available_sorting() -> None:
    """UNICODE collation for sorting should raise CollationError if PyICU not available."""
    event = Event()
    event.add("uid", "123")
    event.add("summary", "Test")

    searcher = Searcher(event=True)
    searcher.add_sort_key("SUMMARY", collation=Collation.UNICODE)

    # Should raise CollationError when trying to generate sort key
    with pytest.raises(CollationError) as exc_info:
        searcher.sorting_value(event)

    assert "PyICU" in str(exc_info.value), "Error should mention PyICU requirement"


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
