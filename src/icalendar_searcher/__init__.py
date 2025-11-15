from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import List
from typing import TYPE_CHECKING
from typing import Union

from icalendar.prop import TypesFactory

if TYPE_CHECKING:
    from icalendar import Calendar
    from icalendar import Component
    from caldav.calendarobjectresource import CalendarObjectResource

types_factory = TypesFactory()


@dataclass
class Searcher:
    """This class will:

    * Allow to build up a calendar search query.
    * Help filterering or sorting a list of calendar components

    Primarily VJOURNAL, VTODO and VEVENT Calendar components are
    intended to be supported, but we should consider if there is any
    point supporting FREEBUSY as well.

    This class is a bit stubbed as of 2025-11, many things not working
    yet.  This class was split out from the CalDAV library and is
    intended for generic search logic not related to the CalDAV
    protocol.  As of 2025-11, the first priority is to make the bare
    minimum of support needed for supporting refactorings of the
    CalDAV library.

    Long-term plan is to also allow for adding subqueries that can be
    bound together with logical AND or OR.  (Will AND every be needed?
    After all, add different criterias to one Searcher object, and all
    of them has to match)

    Properties (like SUMMARY, CATEGORIES, etc) are not meant to be
    sent through the constructor, use the ``add_property_filter``
    method.  Same goes with sort keys, they can be added through the
    ``add_sort_key`` method.

    The ``todo``, ``event`` and ``journal`` parameters are booleans
    for filtering the component type.  If i.e. both todo and
    journal is set to True, everything but events should be returned.
    If none is given (the default), all objects should be returned.

    If ``todo`` is given ``include_completed`` defaults to False,
    which means completed tasks will be tfiltered out.

    ``start`` and ``end`` is giving a time range.  The CalDAV logic
    will be honored, see RFC4791, section 9.9 for very clear
    definitions of what should be returned and what should be filtered
    away.  Timestamps should ideally be with a time zone, if not given
    the local time zone will be assumed.  All-day events may be tricky
    to get correct when timestamps are given and calendar data covers
    multiple time zones.

    ``alarm_start`` and ``alarm_end`` is similar for alarm searching

    If ``expand`` is set to True, recurring objects will be expanded
    into reccurence objects for the time period specified by ``start``
    and ``end``.

    Unless you now what you are doing, ``expand`` should probably be
    set to true - but since ``expand`` can only be combined with a
    start and end, it's by default set to false.

    For filtering an icalendar instance ``mycal`` containing a
    VCALENDAR with multiple independent events, one may do
    ``searcher.filter([mycal])``.  The CalDAV library contains a
    CalDAVSearcher class inheritating this class and including a
    ``.search(caldav_calendar)`` method.  The idea is that it may be
    done in the same way also for searching other calendars or
    calendar-like systems using other protocols.

    The filtering and sorting methods should accept both wrapper
    objects (for the CalDAV library, those are called
    CalendarObjectResource and contains extra information like the URL
    and the client object) and ``icalendar.Calendar`` objects from the
    icalendar library.  Wrapper objects should have the
    ``icalendar.Calendar`` object available through a property
    ``icalendar_instance``.  Even for methods expecting a simple
    component, a ``Calendar`` should be given.  This is of
    imporantance for recurrences with exceptions (like, "daily meeting
    is held at 10:00, except today the meeting is postponed until
    12:00" may be represented through a calendar with two
    subcomponents)

    Methods expecting multiple components will always expect a list of
    calendars (CalDAV-style) - but the algorithms should also be
    robust enough to handle multiple independent components embedded
    in a single Calendar.

    Other ideas that one may consider implementing:
    * limit, offset.
    * fuzzy matching

    """

    todo: bool = None
    event: bool = None
    journal: bool = None
    start: datetime = None
    end: datetime = None
    alarm_start: datetime = None
    alarm_end: datetime = None
    comp_class: Union["CalendarObjectResource", "Component"] = None
    include_completed: bool = None

    expand: bool = False

    _sort_keys: list = field(default_factory=list)
    _property_filters: dict = field(default_factory=dict)
    _property_operator: dict = field(default_factory=dict)

    def add_property_filter(
        self, key: str, value: Any, operator: str = "contains"
    ) -> None:
        """Adds a filter for some specific iCalendar property.

        Examples of valid iCalendar properties: SUMMARY,
        LOCATION, DESCRIPTION, DTSTART, STATUS, CLASS, etc

        :param key: must be an icalendar property, i.e. SUMMARY
        :param value: should adhere to the type defined in the RFC
        :param operator: Comparision operator ("contains", "==", etc)

        For the operator, the following is (planned to be) supported:

        * contains - will do a substring match (A search for "summary"
          "contains" "rain" will return both events with summary
          "Training session" and "Singing in the rain")

        * == - exact match is required

        * ~ - regexp match

        * <, >, <=, >= - comparision

        * <> or != - inqueality, both supported

        * def, undef - will match if the property is (not) defined.  value can be set to None, will be ignored.
        """
        if operator not in ("contains", "undef", "=="):
            raise NotImplementedError(f"The operator {operator} is not supported yet.")
        if operator != "undef":
            self._property_filters[key] = types_factory.for_property(key)(value)
        self._property_operator[key] = operator

    def add_sort_key(self, key: str, reversed: bool = None) -> None:
        """
        Special keys "isnt_overdue" and "hasnt_started" is
        supported, those will compare the DUE (for a task) or the
        DTSTART with the current wall clock and return a bool.

        Except for that, the sort key should be an icalendar property.
        """
        assert key in types_factory.types_map or key in (
            "isnt_overdue",
            "hasnt_started",
        )
        self._sort_keys.append((key, reversed))

    def check_component(
        self, component: Union["Calendar", "CalendarObjectResource"]
    ) -> Union["Calendar", "CalendarObjectResource"]:
        """
        Checks if a component (or recurrence set) matches the filters.  If the component parameter is a calendar containing several independent components, an Exception may be raised.

        * On a match, the component will be returned, otherwise ``None``.
        * If a time specification is given and the component given is a
          recurring component, it will be expanded internally to check if
          it matches the given time specification.
        * If ``self.expand`` is set, the expanded  recurrence set matching
          the time specification will be returned.
        """
        raise NotImplementedError()

    def filter(
        self, components: List[Union["Calendar", "CalendarObjectResource"]]
    ) -> List[Union["Calendar", "CalendarObjectResource"]]:
        """
        Filters the components given according to the search
        criterias, and possibly expanding recurrences.

        This method will not modify the components parameter.  The return
        value is a new list, and if needed it will be containing new objects.
        """
        raise NotImplementedError()

    def sort(
        self, components: List[Union["Calendar", "CalendarObjectResource"]]
    ) -> List[Union["Calendar", "CalendarObjectResource"]]:
        """
        Sorts the components given according to the sort
        keys.

        This method will not modify the components parameter.  The return
        value is a new list, and if needed it will be containing new objects.
        """
        raise NotImplementedError()

    def sort_key(self, component: Union["Calendar", "CalendarObjectResource"]) -> tuple:
        """
        Returns a sortable value from the component, based on the sort keys
        """
        raise NotImplementedError()
