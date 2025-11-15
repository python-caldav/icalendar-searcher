import pytest

from icalendar_searcher import Searcher


def test_add_property_filter_undef() -> None:
    """Adding an "undef" property filter should record the operator but
    not attempt to coerce the value through TypesFactory (since value is
    ignored for 'undef')."""
    s = Searcher()
    s.add_property_filter("SUMMARY", None, operator="undef")
    assert "SUMMARY" in s._property_operator
    assert s._property_operator["SUMMARY"] == "undef"
    assert "SUMMARY" not in s._property_filters


def test_add_property_filter_contains() -> None:
    """Adding a 'contains' property filter should record the operator
    and coerce the value through TypesFactory."""
    s = Searcher()
    s = Searcher()
    s.add_property_filter("SUMMARY", "rain", operator="contains")
    assert "SUMMARY" in s._property_operator
    assert s._property_operator["SUMMARY"] == "contains"
    assert "SUMMARY" in s._property_filters


def test_add_property_filter_unsupported() -> None:
    """Unsupported operators should raise NotImplementedError."""
    s = Searcher()
    with pytest.raises(NotImplementedError):
        s.add_property_filter("SUMMARY", "x", operator="\\o/")


def test_add_sort_key_special() -> None:
    """Special sort keys such as 'isnt_overdue' should be accepted."""
    s = Searcher()
    s.add_sort_key("isnt_overdue", reversed=True)
    assert ("isnt_overdue", True) in s._sort_keys
