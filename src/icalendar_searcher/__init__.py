"""icalendar-searcher: Search and filter iCalendar components.

This package provides the Searcher class for filtering, sorting, and
expanding calendar components (VEVENT, VTODO, VJOURNAL).
"""

## for python 3.9 support
from __future__ import annotations

from .searcher import Searcher

__all__ = ["Searcher"]
