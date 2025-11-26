# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2025-11-26

### Added
- **UNICODE and LOCALE collation support for "==" operator**: The == operator now properly supports UNICODE and LOCALE collations using ICU sort key comparison. Previously only BINARY and CASE_INSENSITIVE collations were supported for exact match operations.

### Fixed
- PyICU-based tests now pass in CI environments where PyICU is installed

## [0.3.1] - 2025-11-26

Some wheel files etc that shouldn't be in the repository has accidentally been added.  Either I've done some silly mistake while sleeping, or perhaps it was a mistake giving the AI access to my computer.

## [0.3.0] - 2025-11-26

Categories are a mess.  I've tried to make a predictable behaviour by making a distinction between `categories` (handling the property filter value as a list that should match or be a subset of the event category set)  and `category` (handling the property filter value as a string that should match towards at least one of the categories in the event).

### Added
- **"category" (singular) property filter**: New virtual property for substring matching within category names
  - `"category"` with "contains" operator does substring matching (e.g., "out" matches "outdoor")
  - `"category"` with "==" operator matches if value exactly equals at least one category name
  - Commas in filter values are treated as literal characters, not split into multiple categories
  - Complements existing `"categories"` (plural) which does exact category name matching

### Fixed
- Category filtering now properly respects collation settings for case-insensitive matching
- Category "contains" operator now correctly checks for subset (exact category names) rather than substring matching
- Category "==" operator now properly supports case-insensitive exact matching
- Text properties with "==" operator now support case-insensitive comparison when `case_sensitive=False`
- Category preprocessing now correctly handles tuples with comma-separated strings

## [0.2.0] - 2025-11-24

Text filtering can be done both case-sensitive and case-insensitive - we need to support both of them.  And we also may need to support various collations.  DISCLAIMER: While I could easily add case insensitive/sensitive filtering myself, as soon as collations was tossed into the equation I considered the AI could do it better and faster than me.  So 0.2.0 is AI-generated code, but curated by a human.

### Added
- **Collation support for text searches and sorting**: Added comprehensive support for both case-sensitive and case-insensitive text comparisons
  - New `case_sensitive` parameter in `add_property_filter()` and `add_sort_key()` methods for simple API
  - New `Collation` enum for power users with support for `BINARY`, `CASE_INSENSITIVE`, `UNICODE`, and `LOCALE` collation strategies
  - Optional PyICU integration for advanced Unicode and locale-aware collation (install with `pip install 'icalendar-searcher[collation]'`)
  - Collation support for all text properties (SUMMARY, LOCATION, DESCRIPTION, etc.)
  - Collation support for CATEGORIES property with special handling
  - Graceful fallback when PyICU is not installed

### Changed
- **BREAKING**: Default text search behavior is now case-sensitive (was case-insensitive)
- Category searches are now case-sensitive by default (was implicitly case-sensitive, now explicit)

### Fixed
- Improved type handling in property filters to correctly distinguish between text properties and other types

## [0.1.10] - Previous Release
