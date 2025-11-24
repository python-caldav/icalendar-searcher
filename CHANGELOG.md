# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
