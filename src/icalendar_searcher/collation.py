"""Text collation support for string comparisons.

This module provides collation (text comparison) functionality with optional
PyICU support for advanced Unicode collation. Falls back to simple binary
and case-insensitive comparisons when PyICU is not available.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum

# Try to import PyICU for advanced collation support
try:
    from icu import Collator as ICUCollator
    from icu import Locale as ICULocale

    HAS_PYICU = True
except ImportError:
    HAS_PYICU = False


class Collation(str, Enum):
    """Text comparison collation strategies.

    For most users, use case_sensitive parameter in add_property_filter()
    instead of working with Collation directly.

    Examples:
        # Simple API (recommended for most users):
        searcher.add_property_filter("SUMMARY", "meeting", case_sensitive=False)

        # Advanced API (for power users):
        searcher.add_property_filter("SUMMARY", "Müller",
                                    collation=Collation.LOCALE,
                                    locale="de_DE")
    """

    BINARY = "binary"
    """Exact byte-for-byte comparison (case-sensitive)."""

    CASE_INSENSITIVE = "case_insensitive"
    """Case-insensitive comparison using Python's str.lower()."""

    UNICODE = "unicode"
    """Unicode Collation Algorithm (UCA) root collation.
    Requires PyICU to be installed."""

    LOCALE = "locale"
    """Locale-aware collation using CLDR rules.
    Requires PyICU to be installed and locale parameter."""


class CollationError(Exception):
    """Raised when collation operation cannot be performed."""

    pass


def get_collation_function(
    collation: Collation = Collation.BINARY,
    locale: str | None = None,
) -> Callable[[str, str], bool]:
    """Get a collation function for substring matching.

    Args:
        collation: The collation strategy to use
        locale: Locale string (e.g., "de_DE", "en_US") for LOCALE collation

    Returns:
        A function that takes (needle, haystack) and returns True if needle
        is found in haystack according to the collation rules.

    Raises:
        CollationError: If PyICU is required but not available, or if
                       invalid parameters are provided.

    Examples:
        >>> match_fn = get_collation_function(Collation.CASE_INSENSITIVE)
        >>> match_fn("test", "This is a TEST")
        True
    """
    if collation == Collation.BINARY:
        return _binary_contains

    elif collation == Collation.CASE_INSENSITIVE:
        return _case_insensitive_contains

    elif collation in (Collation.UNICODE, Collation.LOCALE):
        if not HAS_PYICU:
            raise CollationError(
                f"Collation '{collation}' requires PyICU to be installed. "
                "Install with: pip install 'icalendar-searcher[collation]'"
            )

        if collation == Collation.LOCALE:
            if not locale:
                raise CollationError("LOCALE collation requires a locale parameter")
            return _get_icu_contains(locale)
        else:
            # UNICODE collation uses root locale
            return _get_icu_contains(None)

    else:
        raise CollationError(f"Unknown collation: {collation}")


def get_sort_key_function(
    collation: Collation = Collation.BINARY,
    locale: str | None = None,
) -> Callable[[str], bytes]:
    """Get a collation function for generating sort keys.

    Args:
        collation: The collation strategy to use
        locale: Locale string (e.g., "de_DE", "en_US") for LOCALE collation

    Returns:
        A function that takes a string and returns a sort key (bytes) that
        can be used for sorting according to the collation rules.

    Raises:
        CollationError: If PyICU is required but not available, or if
                       invalid parameters are provided.

    Examples:
        >>> sort_key_fn = get_sort_key_function(Collation.CASE_INSENSITIVE)
        >>> sorted(["Zebra", "apple", "Banana"], key=sort_key_fn)
        ['apple', 'Banana', 'Zebra']
    """
    if collation == Collation.BINARY:
        return lambda s: s.encode("utf-8")

    elif collation == Collation.CASE_INSENSITIVE:
        return lambda s: s.lower().encode("utf-8")

    elif collation in (Collation.UNICODE, Collation.LOCALE):
        if not HAS_PYICU:
            raise CollationError(
                f"Collation '{collation}' requires PyICU to be installed. "
                "Install with: pip install 'icalendar-searcher[collation]'"
            )

        if collation == Collation.LOCALE:
            if not locale:
                raise CollationError("LOCALE collation requires a locale parameter")
            return _get_icu_sort_key(locale)
        else:
            # UNICODE collation uses root locale
            return _get_icu_sort_key(None)

    else:
        raise CollationError(f"Unknown collation: {collation}")


# ============================================================================
# Internal implementation functions
# ============================================================================


def _binary_contains(needle: str, haystack: str) -> bool:
    """Binary (case-sensitive) substring match."""
    return needle in haystack


def _case_insensitive_contains(needle: str, haystack: str) -> bool:
    """Case-insensitive substring match."""
    return needle.lower() in haystack.lower()


def _get_icu_contains(locale: str | None) -> Callable[[str, str], bool]:
    """Get ICU-based substring matcher.

    Note: This is a simplified implementation. PyICU doesn't expose ICU's
    StringSearch API which would be needed for proper substring matching with
    collation. For now, we use case-insensitive matching as an approximation.

    Future enhancement: Implement proper collation-aware substring matching.
    """

    def icu_contains(needle: str, haystack: str) -> bool:
        """Check if needle is in haystack using case-insensitive matching.

        This is a fallback implementation until proper ICU StringSearch support
        is added. It provides reasonable behavior for most use cases.
        """
        # TODO: Use ICU StringSearch for proper collation-aware substring matching
        # For now, fall back to case-insensitive as a reasonable approximation
        return needle.lower() in haystack.lower()

    return icu_contains


def _get_icu_sort_key(locale: str | None) -> Callable[[str], bytes]:
    """Get ICU-based sort key function.

    Creates a collator instance and returns a function that generates sort keys.
    The collator is configured for case-insensitive comparison (SECONDARY strength).
    """
    icu_locale = ICULocale(locale) if locale else ICULocale.getRoot()
    collator = ICUCollator.createInstance(icu_locale)

    # Set strength to SECONDARY for case-insensitive comparison
    # PRIMARY = base character differences only
    # SECONDARY = base + accent differences (case-insensitive)
    # TERTIARY = base + accent + case differences (default, case-sensitive)
    collator.setStrength(ICUCollator.SECONDARY)

    def icu_sort_key(s: str) -> bytes:
        """Generate ICU collation sort key."""
        return collator.getSortKey(s)

    return icu_sort_key
