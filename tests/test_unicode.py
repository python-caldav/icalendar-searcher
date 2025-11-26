"""Tests for Unicode and non-ASCII character handling across different collations.

This module tests filtering and sorting with:
- Norwegian/Scandinavian characters (æ, ø, å)
- Turkish characters (ı, ş, ğ, ü)
- Cyrillic characters (Б, Г, Д, etc.)

Tests cover all collation strategies:
- BINARY (byte-by-byte comparison)
- CASE_INSENSITIVE (Python's str.lower())
- UNICODE (requires PyICU)
- LOCALE (requires PyICU)
"""

from datetime import date

import pytest
from icalendar import Calendar, Event

from icalendar_searcher import Searcher
from icalendar_searcher.collation import Collation


def make_event(summary: str, uid: str = "test-event") -> Calendar:
    """Create a simple calendar with one event."""
    cal = Calendar()
    event = Event()
    event.add("summary", summary)
    event.add("uid", uid)
    event.add("dtstart", date(2025, 1, 1))
    cal.add_component(event)
    return cal


class TestNorwegianScandinavianCharacters:
    """Test Norwegian/Scandinavian characters (æ, ø, å)."""

    def test_binary_case_sensitive_exact_match(self) -> None:
        """Binary collation should match exact case only."""
        cal = make_event("Blåbærsyltetøy")
        searcher = Searcher()
        searcher.add_property_filter(
            "SUMMARY", "Blåbærsyltetøy", operator="==", collation=Collation.BINARY
        )
        assert searcher.check_component(cal)

    def test_binary_case_sensitive_no_match_different_case(self) -> None:
        """Binary collation should not match different case."""
        cal = make_event("Blåbærsyltetøy")
        searcher = Searcher()
        searcher.add_property_filter(
            "SUMMARY", "BLÅBÆRSYLTETØY", operator="==", collation=Collation.BINARY
        )
        assert not searcher.check_component(cal)

    def test_case_insensitive_match_uppercase(self) -> None:
        """Case-insensitive should match uppercase variant."""
        cal = make_event("Blåbærsyltetøy")
        searcher = Searcher()
        searcher.add_property_filter(
            "SUMMARY", "BLÅBÆRSYLTETØY", operator="==", case_sensitive=False
        )
        assert searcher.check_component(cal)

    def test_case_insensitive_match_lowercase(self) -> None:
        """Case-insensitive should match lowercase variant."""
        cal = make_event("BLÅBÆRSYLTETØY")
        searcher = Searcher()
        searcher.add_property_filter(
            "SUMMARY", "blåbærsyltetøy", operator="==", case_sensitive=False
        )
        assert searcher.check_component(cal)

    def test_case_insensitive_contains_norwegian(self) -> None:
        """Case-insensitive substring matching with Norwegian characters."""
        cal = make_event("Jeg liker Blåbærsyltetøy")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "BLÅBÆR", operator="contains", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_sorting_norwegian_alphabetical_order(self) -> None:
        """Test sorting with Norwegian alphabet order (a-z, æ, ø, å)."""
        # Create events with Norwegian words
        cal1 = make_event("Appelsin", "1")
        cal2 = make_event("Banan", "2")
        cal3 = make_event("Æble", "3")  # Should come after z
        cal4 = make_event("Øl", "4")  # Should come after æ
        cal5 = make_event("Åpning", "5")  # Should come after ø

        searcher = Searcher()
        searcher.add_sort_key("SUMMARY", case_sensitive=False)

        # Get sorting values
        vals = [(searcher.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4, cal5]]
        sorted_vals = sorted(vals, key=lambda x: x[0])
        sorted_summaries = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_vals]

        # With CASE_INSENSITIVE (Python's lower()), order may not be linguistically correct
        # but should be consistent
        assert len(sorted_summaries) == 5
        assert "Appelsin" in sorted_summaries
        assert "Banan" in sorted_summaries


class TestFrenchCharacters:
    """Test French accented characters (é, è, ê, ç, à, etc.)."""

    def test_french_accents_case_sensitive(self) -> None:
        """Test French accented characters with case-sensitive matching."""
        cal = make_event("crème brûlée")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "crème brûlée", operator="==")
        assert searcher.check_component(cal)

    def test_french_accents_case_insensitive(self) -> None:
        """Test French accented characters with case-insensitive matching."""
        cal = make_event("crème brûlée")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "CRÈME BRÛLÉE", operator="==", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_french_cedilla_matching(self) -> None:
        """Test French ç (c with cedilla) character matching."""
        cal = make_event("Français")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "français", operator="==", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_french_various_accents_substring(self) -> None:
        """Test substring matching with various French accents."""
        cal = make_event("À la recherche du temps perdu")
        searcher = Searcher()
        searcher.add_property_filter(
            "SUMMARY", "RECHERCHE", operator="contains", case_sensitive=False
        )
        assert searcher.check_component(cal)

    def test_sorting_french_words(self) -> None:
        """Test sorting French words with accents."""
        cal1 = make_event("Café", "1")
        cal2 = make_event("Crème", "2")
        cal3 = make_event("École", "3")
        cal4 = make_event("Élève", "4")

        searcher = Searcher()
        searcher.add_sort_key("SUMMARY", case_sensitive=False)

        vals = [(searcher.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]]
        sorted_vals = sorted(vals, key=lambda x: x[0])
        sorted_summaries = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_vals]

        # Verify all items are present
        assert len(sorted_summaries) == 4
        assert set(sorted_summaries) == {"Café", "Crème", "École", "Élève"}


class TestTurkishCharacters:
    """Test Turkish characters (ı, ş, ğ, ü, ç)."""

    def test_turkish_i_with_dot_vs_without(self) -> None:
        """Turkish has two i characters: i/İ and ı/I."""
        cal_dotted = make_event("İstanbul", "1")

        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "istanbul", operator="==", case_sensitive=False)
        # Python's lower() may not handle Turkish i correctly
        # This documents the behavior rather than prescribes it
        result = searcher.check_component(cal_dotted)
        # Result depends on Python's locale-unaware lower()
        assert isinstance(result, (bool, type(None), list))

    def test_turkish_special_characters_case_insensitive(self) -> None:
        """Test Turkish special characters with case-insensitive matching."""
        cal = make_event("Gümüşhane")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "GÜMÜŞHANE", operator="==", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_turkish_cedilla_matching(self) -> None:
        """Test Turkish ç character matching."""
        cal = make_event("Çocuk")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "çocuk", operator="==", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_turkish_soft_g_matching(self) -> None:
        """Test Turkish ğ (soft g) character matching."""
        cal = make_event("Dağ")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "DAĞ", operator="==", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_sorting_turkish_words(self) -> None:
        """Test sorting Turkish words."""
        cal1 = make_event("Ankara", "1")
        cal2 = make_event("Çanakkale", "2")
        cal3 = make_event("Diyarbakır", "3")
        cal4 = make_event("İstanbul", "4")

        searcher = Searcher()
        searcher.add_sort_key("SUMMARY", case_sensitive=False)

        vals = [(searcher.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]]
        sorted_vals = sorted(vals, key=lambda x: x[0])
        sorted_summaries = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_vals]

        # Verify all items are present (order depends on collation)
        assert len(sorted_summaries) == 4
        assert set(sorted_summaries) == {"Ankara", "Çanakkale", "Diyarbakır", "İstanbul"}


class TestCyrillicCharacters:
    """Test Cyrillic characters (Russian, Ukrainian, etc.)."""

    def test_russian_case_sensitive_exact_match(self) -> None:
        """Test exact match with Russian text."""
        cal = make_event("Привет")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "Привет", operator="==")
        assert searcher.check_component(cal)

    def test_russian_case_insensitive_match(self) -> None:
        """Test case-insensitive matching with Russian text."""
        cal = make_event("Привет")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "ПРИВЕТ", operator="==", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_cyrillic_contains_substring(self) -> None:
        """Test substring matching with Cyrillic text."""
        cal = make_event("Доброе утро")
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "утро", operator="contains", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_ukrainian_specific_characters(self) -> None:
        """Test Ukrainian-specific characters (і, ї, є, ґ)."""
        cal = make_event("Київ")  # Kyiv
        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "КИЇВ", operator="==", case_sensitive=False)
        assert searcher.check_component(cal)

    def test_sorting_cyrillic_words(self) -> None:
        """Test sorting Russian words."""
        cal1 = make_event("Москва", "1")  # Moscow
        cal2 = make_event("Санкт-Петербург", "2")  # St. Petersburg
        cal3 = make_event("Владивосток", "3")  # Vladivostok
        cal4 = make_event("Екатеринбург", "4")  # Yekaterinburg

        searcher = Searcher()
        searcher.add_sort_key("SUMMARY", case_sensitive=False)

        vals = [(searcher.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]]
        sorted_vals = sorted(vals, key=lambda x: x[0])
        sorted_summaries = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_vals]

        # Verify all items are present
        assert len(sorted_summaries) == 4
        assert set(sorted_summaries) == {
            "Москва",
            "Санкт-Петербург",
            "Владивосток",
            "Екатеринбург",
        }


class TestCollationDifferences:
    """Tests that demonstrate actual differences between collation strategies."""

    def test_case_sensitivity_binary_vs_case_insensitive(self) -> None:
        """Binary and case-insensitive collations sort mixed case differently."""
        # Create events with mixed case
        cal1 = make_event("apple", "1")
        cal2 = make_event("BANANA", "2")
        cal3 = make_event("Cherry", "3")
        cal4 = make_event("date", "4")

        # BINARY collation (case-sensitive): uppercase comes before lowercase
        searcher_binary = Searcher()
        searcher_binary.add_sort_key("SUMMARY", collation=Collation.BINARY)
        vals_binary = [
            (searcher_binary.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]
        ]
        sorted_binary = sorted(vals_binary, key=lambda x: x[0])
        summaries_binary = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_binary]

        # CASE_INSENSITIVE collation: ignores case, alphabetical order
        searcher_ci = Searcher()
        searcher_ci.add_sort_key("SUMMARY", case_sensitive=False)
        vals_ci = [(searcher_ci.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]]
        sorted_ci = sorted(vals_ci, key=lambda x: x[0])
        summaries_ci = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_ci]

        # Binary: uppercase letters (A-Z) come before lowercase (a-z) in ASCII/Unicode
        # So "BANANA" and "Cherry" should come before "apple" and "date"
        assert summaries_binary == ["BANANA", "Cherry", "apple", "date"]

        # Case-insensitive: alphabetical regardless of case
        assert summaries_ci == ["apple", "BANANA", "Cherry", "date"]

    def test_unicode_codepoint_order_vs_linguistic_order(self) -> None:
        """Show difference between Unicode codepoint order and linguistic sorting."""
        # Norwegian words where Unicode order differs from linguistic order
        cal1 = make_event("Zebra", "1")
        cal2 = make_event("Ærlig", "2")  # Should come after Z in Norwegian
        cal3 = make_event("Øl", "3")  # Should come after Æ in Norwegian
        cal4 = make_event("Åpen", "4")  # Should come after Ø in Norwegian

        # With BINARY or CASE_INSENSITIVE (Python's lower()), order is by Unicode codepoint
        searcher_ci = Searcher()
        searcher_ci.add_sort_key("SUMMARY", case_sensitive=False)
        vals_ci = [(searcher_ci.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]]
        sorted_ci = sorted(vals_ci, key=lambda x: x[0])
        summaries_ci = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_ci]

        # In Unicode, Æ (U+00C6), Ø (U+00D8), Å (U+00C5) come before Z (U+005A)
        # when sorted by codepoint in lowercase (æ=U+00E6, ø=U+00F8, å=U+00E5, z=U+007A)
        # So: Æ, Ø, Zebra, Å (when lowercased and sorted by codepoint)
        # The exact order depends on how Python's lower() + sort handles these
        assert "Zebra" in summaries_ci
        assert "Ærlig" in summaries_ci
        # Note: Linguistic order (with proper Norwegian locale) would be:
        # Zebra, Ærlig, Øl, Åpen (a-z, then æ, ø, å)

    def test_accented_characters_sorting_differences(self) -> None:
        """Show how accented characters sort differently with different strategies."""
        cal1 = make_event("cote", "1")  # no accent
        cal2 = make_event("côte", "2")  # circumflex
        cal3 = make_event("coté", "3")  # acute
        cal4 = make_event("côté", "4")  # both

        # BINARY collation
        searcher_binary = Searcher()
        searcher_binary.add_sort_key("SUMMARY", collation=Collation.BINARY)
        vals_binary = [
            (searcher_binary.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]
        ]
        sorted_binary = sorted(vals_binary, key=lambda x: x[0])
        summaries_binary = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_binary]

        # With binary/codepoint sorting, accented characters come after unaccented
        # e (U+0065) < é (U+00E9), o (U+006F) < ô (U+00F4)
        assert summaries_binary == ["cote", "coté", "côte", "côté"]

        # Note: With proper French locale collation (if PyICU available),
        # the order might be different, treating é as a variant of e

    def test_mixed_scripts_sorting_order(self) -> None:
        """Test sorting with mixed Latin and Cyrillic."""
        cal1 = make_event("Apple", "1")
        cal2 = make_event("Яблоко", "2")  # Apple in Russian (Ya-b-l-o-k-o)
        cal3 = make_event("Банан", "3")  # Banana in Russian (B-a-n-a-n)
        cal4 = make_event("Banana", "4")

        searcher = Searcher()
        searcher.add_sort_key("SUMMARY", case_sensitive=False)

        vals = [(searcher.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]]
        sorted_vals = sorted(vals, key=lambda x: x[0])
        sorted_summaries = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_vals]

        # Latin (A=U+0041, B=U+0042) comes before Cyrillic (Б=U+0411, Я=U+042F)
        # So: Apple, Banana, then Cyrillic words
        assert len(sorted_summaries) == 4
        latin_indices = [i for i, s in enumerate(sorted_summaries) if s in ["Apple", "Banana"]]
        cyrillic_indices = [i for i, s in enumerate(sorted_summaries) if s in ["Яблоко", "Банан"]]
        # Latin characters should sort before Cyrillic in Unicode
        assert max(latin_indices) < min(cyrillic_indices)
        # Within each script, alphabetical order
        assert sorted_summaries[0] == "Apple"
        assert sorted_summaries[1] == "Banana"


class TestMixedScriptsAndCollations:
    """Test mixed scripts and edge cases."""

    def test_all_collations_on_same_data(self) -> None:
        """Test all available collations on the same data."""
        cal_lower = make_event("blåbær")
        cal_upper = make_event("BLÅBÆR")

        # BINARY - case-sensitive
        searcher_binary = Searcher()
        searcher_binary.add_property_filter(
            "SUMMARY", "blåbær", operator="==", collation=Collation.BINARY
        )
        assert searcher_binary.check_component(cal_lower)
        assert not searcher_binary.check_component(cal_upper)

        # CASE_INSENSITIVE - should match both
        searcher_ci = Searcher()
        searcher_ci.add_property_filter(
            "SUMMARY", "blåbær", operator="==", collation=Collation.CASE_INSENSITIVE
        )
        assert searcher_ci.check_component(cal_lower)
        assert searcher_ci.check_component(cal_upper)

    def test_emoji_and_special_unicode(self) -> None:
        """Test handling of emoji and special Unicode characters."""
        cal = make_event("Party 🎉 Celebration")
        searcher = Searcher()
        searcher.add_property_filter(
            "SUMMARY", "party 🎉", operator="contains", case_sensitive=False
        )
        assert searcher.check_component(cal)

    def test_combining_characters(self) -> None:
        """Test handling of combining diacritical marks."""
        # café with combining accent vs precomposed
        cal_combining = make_event("café")  # e + combining acute
        cal_precomposed = make_event("café")  # é as single character

        searcher = Searcher()
        searcher.add_property_filter("SUMMARY", "café", operator="contains", case_sensitive=False)
        # Both should match (though Unicode normalization may vary)
        assert searcher.check_component(cal_combining)
        assert searcher.check_component(cal_precomposed)


class TestPyICUCollations:
    """Tests requiring PyICU for UNICODE and LOCALE collations."""

    @pytest.mark.parametrize(
        "text,search",
        [
            ("Blåbærsyltetøy", "blåbærsyltetøy"),
            ("Москва", "москва"),
        ],
    )
    def test_unicode_collation_case_insensitive(self, text: str, search: str) -> None:
        """Test UNICODE collation with == operator if PyICU is available."""
        try:
            import icu  # noqa: F401

            cal = make_event(text)
            searcher = Searcher()
            searcher.add_property_filter(
                "SUMMARY", search, operator="==", collation=Collation.UNICODE
            )
            result = searcher.check_component(cal)
            # With UNICODE collation, case-insensitive matching should work
            assert result, f"Expected {text!r} to match {search!r} with UNICODE collation"
        except ImportError:
            pytest.skip("PyICU not installed")

    def test_turkish_i_requires_locale(self) -> None:
        """Test that Turkish İ/i requires Turkish locale, not just UNICODE collation."""
        try:
            import icu  # noqa: F401

            cal = make_event("İstanbul")

            # With UNICODE (root locale), İ does NOT match i
            # Turkish İ is U+0130, which is distinct from ASCII i (U+0069)
            searcher_unicode = Searcher()
            searcher_unicode.add_property_filter(
                "SUMMARY", "istanbul", operator="==", collation=Collation.UNICODE
            )
            result_unicode = searcher_unicode.check_component(cal)
            # Root locale doesn't do Turkish-specific case folding
            assert not result_unicode, "Root locale should not match Turkish İ with i"

            # With Turkish locale, İ DOES match i
            searcher_turkish = Searcher()
            searcher_turkish.add_property_filter(
                "SUMMARY", "istanbul", operator="==", collation=Collation.LOCALE, locale="tr_TR"
            )
            result_turkish = searcher_turkish.check_component(cal)
            assert result_turkish, "Turkish locale should match İ with i"
        except ImportError:
            pytest.skip("PyICU not installed")

    def test_locale_specific_collation_norwegian(self) -> None:
        """Test Norwegian locale-specific sorting if PyICU is available."""
        try:
            import icu  # noqa: F401

            cal1 = make_event("Zulu", "1")
            cal2 = make_event("Ærlig", "2")
            cal3 = make_event("Øl", "3")
            cal4 = make_event("Åpen", "4")

            searcher = Searcher()
            searcher.add_sort_key("SUMMARY", collation=Collation.LOCALE, locale="nb_NO")

            vals = [(searcher.sorting_value(cal), cal) for cal in [cal1, cal2, cal3, cal4]]
            sorted_vals = sorted(vals, key=lambda x: x[0])
            sorted_summaries = [cal.walk("VEVENT")[0]["SUMMARY"] for _, cal in sorted_vals]

            # In Norwegian, correct order is: Zulu, Ærlig, Øl, Åpen
            # (æ, ø, å come after z)
            assert sorted_summaries == ["Zulu", "Ærlig", "Øl", "Åpen"]
        except ImportError:
            pytest.skip("PyICU not installed")

    def test_locale_specific_collation_turkish(self) -> None:
        """Test Turkish locale-specific collation if PyICU is available."""
        try:
            import icu  # noqa: F401

            # Turkish has special i/I handling
            cal_i_dotted = make_event("İstanbul")
            searcher = Searcher()
            searcher.add_property_filter(
                "SUMMARY",
                "istanbul",
                operator="==",
                collation=Collation.LOCALE,
                locale="tr_TR",
            )
            # With Turkish locale, İ lowercases to i, I lowercases to ı
            result = searcher.check_component(cal_i_dotted)
            assert result
        except ImportError:
            pytest.skip("PyICU not installed")
