from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from itertools import tee
from typing import TYPE_CHECKING, Any, Union

import recurring_ical_events
from icalendar import Calendar, Component, Timezone, error
from icalendar.prop import TypesFactory
from recurring_ical_events import DATE_MAX_DT, DATE_MIN_DT

if TYPE_CHECKING:
    from caldav.calendarobjectresource import CalendarObjectResource

## We need an instance of the icalendar.prop.TypesFactory class.
## We'll make a global instance rather than instantiate it for
## every loop ieration
types_factory = TypesFactory()


## Helper to normalize date/datetime for comparison
## (I feel this one is duplicated over many projects ...)
def _normalize_dt(dt_value: date | datetime) -> datetime:
    """Convert date to datetime for comparison, or return datetime as-is with timezone."""
    if dt_value is None:
        return None
    ## If it's a date (not datetime), convert to datetime at midnight
    if hasattr(dt_value, "year") and not hasattr(dt_value, "hour"):
        from datetime import time

        return datetime.combine(dt_value, time.min).astimezone()
    ## TODO: we should probably do some research on the default calendar timezone,
    ## which may not be the same as the local timezone ... uh ... timezones are
    ## difficult.
    return dt_value.astimezone()


## Helper - generators are generally more neat than lists,
## but bool(x) will always return True.  I'd like to verify
## that a generator is not empty, without side effects.
def _iterable_or_false(g: Iterable, _debug_print_peek: bool = False) -> bool | Iterable:
    """This method will return False if it's not possible to get an
    item from the iterable (which can only be done by utilizing
    `next`).  It will then return a new iterator that behaves like
    the original iterator (like if `next` wasn't used).

    Uses itertools.tee to create two independent iterators: one for
    checking if the iterator is empty, and one to return.
    """
    if not isinstance(g, Iterator):
        return bool(g) and g

    # Create two independent iterators from the input
    check_it, result_it = tee(g)

    try:
        my_value = next(check_it)
        if _debug_print_peek:
            print(my_value)
        return result_it  # Return the untouched iterator
    except StopIteration:
        return False


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
    sent through the constructor, use the :func:`icalendar_searcher.Searcher.add_property_filter`
    method.  Same goes with sort keys, they can be added through the
    `func:icalendar_searcher.Searcher.add_sort_key` method.

    The ``todo``, ``event`` and ``journal`` parameters are booleans
    for filtering the component type.  If i.e. both todo and
    journal is set to True, everything but events should be returned.
    If none is given (the default), all objects should be returned.

    If ``todo`` is given ``include_completed`` defaults to False,
    which means completed tasks will be tfiltered out.

    ``start`` and ``end`` is giving a time range.  RFC4791, section
    9.9 gives a very clear and sane definitions of what should be
    returned when searching a CalDAV calendar for contents over a time
    span.  While this package is not related to CalDAV pper se, the
    logic seems sane, so we will stick to that one.  Timestamps should
    ideally be with a time zone, if not given the local time zone will
    be assumed.  All-day events may be tricky to get correct when
    timestamps are given and calendar data covers multiple time zones.

    ``alarm_start`` and ``alarm_end`` is similar for alarm searching

    If ``expand`` is set to True, recurring objects will be expanded
    into reccurence objects for the time period specified by ``start``
    and ``end``.  Generators are used, so ``expand`` may even work
    without ``start`` and ``end`` set if care is taken
    (i.e. converting the generator to a list may cause problems)

    Unless you now what you are doing, ``expand`` should probably be
    set to true, and start and end should be given and shouldn't be
    too far away from each other.  Currently the sorting algorithm
    will blow up if the expand yields infinite number of events.  It
    may probably blow up even if expand yields millions of events.  Be
    careful.

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
    include_completed: bool = None

    expand: bool = False

    _sort_keys: list = field(default_factory=list)
    _property_filters: dict = field(default_factory=dict)
    _property_operator: dict = field(default_factory=dict)

    def add_property_filter(self, key: str, value: Any, operator: str = "contains") -> None:
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
        self,
        component: Union["Calendar", "Component", "CalendarObjectResource"],
        expand_only: bool = False,
        _ignore_rrule_and_time: bool = False,
    ) -> Iterable["Component"]:
        """Checks if one component (or recurrence set) matches the
        filters.  If the component parameter is a calendar containing
        several independent components, an Exception may be raised,
        though recurrence sets should be suppored.

        * If there is no match, ``None`` or ``False`` will be returned
          (the exact return value is currently not clearly defined,
          but ``bool(return_value)`` should yield False).

        * If a time specification is given and the component given is
          a recurring component, it will be expanded internally to
          check if it matches the given time specification.

        * If there is a match, the component should be returned
          (wrapped in a tuple) - unless ``expand`` is set, in which
          case all matching recurrences will be returned (as a
          generator object).

        :param component: Todo, Event, Calendar or such
        :param expand_only: Don't do any filtering, just expand

        """
        ## For consistant and predictable return value, we need to
        ## transform the component in the very start.  We need to make
        ## it into a list so we can iterate on it without throwing
        ## away data.  TODO: This will break badly if the
        ## component already is a generator with infinite amount of
        ## recurrences.  It should be possible to fix this in a smart
        ## way.  I.e., make a new wrappable class ListLikeGenerator
        ## that stores the elements we've taken out from the
        ## generator.  Such a class would also eliminate the need of
        ## _generator_or_false.
        orig_recurrence_set = self._validate_and_normalize_component(component)

        ## Early return if no work needed
        if expand_only and not self.expand:
            return orig_recurrence_set

        ## Ensure timezone is set.  Ensure start and end are datetime objects.
        for attr in ("start", "end", "alarm_start", "alarm_end"):
            value = getattr(self, attr)
            if value:
                if not isinstance(value, datetime):
                    raise NotImplementedError("Date-range searches not supported yet; use datetime")
                setattr(self, attr, _normalize_dt(value))

        ## recurrence_set is our internal generator/iterator containing
        ## everything that hasn't been filtered out yet (in most
        ## cases, the generator will yield either one or zero
        ## components - but recurrences are tricky).  orig_recurrence_set
        ## is a list, so iterations on recurrence_set will not affect
        ## orig_recurrence_set
        recurrence_set = orig_recurrence_set

        ## Recurrences may be a night-mare.
        ## I'm not sure if this is very well thought through, but my thoughts now are:

        ## 1) we need to check if the not-expanded base element
        ## matches any non-date-related search-filters before doing
        ## anything else.  We do this with a recursive call with an
        ## internal parameter _ignore_rrule_and_time set.

        ## 2) If the base element does not match, we may probably skip
        ## expansion (only problem I can see with it is some filtering
        ## like "show me all events happening on a Monday" - which is
        ## anyway not supported as for now).  It's important to skip
        ## expansion, otherwise we may end up doing an infinite (or
        ## very-huge) expansion just to verify that we can return
        ## None/False

        ## 3) if the base element does not match, there may still be
        ## special cases matching.  We solve this by running the
        ## filter logics on all but the

        ## 4) if the base element matches, we may need to expand it
        first = orig_recurrence_set[0]
        if not expand_only and "rrule" in first and not _ignore_rrule_and_time:
            ## TODO: implement logic above
            base_element_match = self.check_component(first, _ignore_rrule_and_time=True)
            if not base_element_match:
                ## Base element is to be ignored.  recurrence_set is still a list
                recurrence_set = recurrence_set[1:]  # Remove first element (base), keep exceptions

        ## self.include_completed should default to False if todo is explicity set,
        ## otherwise True
        if self.include_completed is None:
            self.include_completed = not self.todo

        ## Component type flags are a bit difficult.  In the CalDAV library,
        ## if all of them are None, everything should be returned.  If only
        ## one of them is True, then only this kind of component type is
        ## returned.  In any other case, no guarantees of correctness are given.

        ## Let's skip the last remark and try to make a generic and
        ## correct solution from the start: 1) if any flags are True,
        ## then consider flags set as None as False.  2) if any flags
        ## are still None, then consider those to be True.  3) List
        ## the flags that are True as acceptable component types:

        comptypesl = ("todo", "event", "journal")
        if any(getattr(self, x) for x in comptypesl):
            for x in comptypesl:
                if getattr(self, x) is None:
                    setattr(self, x, False)
        else:
            for x in comptypesl:
                if getattr(self, x) is None:
                    setattr(self, x, True)

        comptypesu = set([f"V{x.upper()}" for x in comptypesl if getattr(self, x)])

        ## if expand_only, expand all comptypes, otherwise only the comptypes specified in the filters
        comptypes_for_expansion = ['VTODO', 'VEVENT', 'VJOURNAL'] if expand_only else comptypesu

        if not _ignore_rrule_and_time and "rrule" in first:
            recurrence_set = self._expand_recurrences(recurrence_set, comptypes_for_expansion)

        if not expand_only:
            ## OPTIMIZATION TODO: If the object was recurring, we should
            ## probably trust recur.between to do the right thing?
            if not _ignore_rrule_and_time and (self.start or self.end):
                recurrence_set = (x for x in recurrence_set if self._check_range(x))

            ## This if is just to save some few CPU cycles - skip filtering if it's not needed
            if not all(getattr(self, x) for x in comptypesl):
                recurrence_set = (x for x in recurrence_set if x.name in comptypesu)

            ## Filter based on include_completed setting
            recurrence_set = (x for x in recurrence_set if self._check_completed_filter(x))

            ## Apply property filters
            if self._property_filters or self._property_operator:
                recurrence_set = (x for x in recurrence_set if self._check_property_filters(x))

            ## Apply alarm filters
            if not _ignore_rrule_and_time and (self.alarm_start or self.alarm_end):
                recurrence_set = (x for x in recurrence_set if self._check_alarm_range(x))

        if self.expand:
            ## TODO: fix wrapping, if needed
            return _iterable_or_false(recurrence_set)
        else:
            if next(recurrence_set, None):
                return orig_recurrence_set
            else:
                return None

    def filter(
        self, components: list[Union["Calendar", "CalendarObjectResource"]]
    ) -> list[Union["Calendar", "CalendarObjectResource"]]:
        """
        Filters the components given according to the search
        criterias, and possibly expanding recurrences.

        This method will not modify the components parameter.  The return
        value is a new list, and if needed it will be containing new objects.
        """
        raise NotImplementedError()

    def sort(
        self, components: list[Union["Calendar", "CalendarObjectResource"]]
    ) -> list[Union["Calendar", "CalendarObjectResource"]]:
        """
        Sorts the components given according to the sort
        keys.

        This method will not modify the components parameter.  The return
        value is a new list, and if needed it will be containing new objects.
        """
        raise NotImplementedError()

    def sorting_value(self, component: Union["Calendar", "CalendarObjectResource"]) -> tuple:
        """
        Returns a sortable value from the component, based on the sort keys
        """
        ret = []
        ## TODO: this logic has been moved more or less as-is from the
        ## caldav library.  It may need some rethinking and QA work.

        ## TODO: we disregard any complexity wrg of recurring events
        component = self._unwrap(component)

        not_tz_components = (x for x in component.subcomponents if not isinstance(x, Timezone))
        comp = next(not_tz_components)

        defaults = {
            ## TODO: all possible non-string sort attributes needs to be listed here, otherwise we will get type errors when comparing objects with the property defined vs undefined (or maybe we should make an "undefined" object that always will compare below any other type?  Perhaps there exists such an object already?)
            "due": "2050-01-01",
            "dtstart": "1970-01-01",
            "priority": 0,
            "status": {
                "VTODO": "NEEDS-ACTION",
                "VJOURNAL": "FINAL",
                "VEVENT": "TENTATIVE",
            }[comp.name],
            "category": "",
            ## Usage of strftime is a simple way to ensure there won't be
            ## problems if comparing dates with timestamps
            "isnt_overdue": not (
                "due" in comp
                and comp["due"].dt.strftime("%F%H%M%S") < datetime.now().strftime("%F%H%M%S")
            ),
            "hasnt_started": (
                "dtstart" in comp
                and comp["dtstart"].dt.strftime("%F%H%M%S") > datetime.now().strftime("%F%H%M%S")
            ),
        }
        for sort_key, reverse in self._sort_keys:
            val = comp.get(sort_key, None)
            if val is None:
                ret.append(defaults.get(sort_key.lower(), ""))
                continue
            if hasattr(val, "dt"):
                val = val.dt
            elif hasattr(val, "cats"):
                val = ",".join(val.cats)
            if hasattr(val, "strftime"):
                val = val.strftime("%F%H%M%S")
            if reverse:
                if isinstance(val, str):
                    val = val.encode()
                    val = bytes(b ^ 0xFF for b in val)
                else:
                    val = -val
            ret.append(val)

        return ret

    def _unwrap(self, component: Union["Calendar", "CalendarObjectResource"]) -> "Calendar":
        """
        To support the caldav library (and possibly other libraries where the
        icalendar component is wrapped)
        """
        try:
            component = component.icalendar_instance
        except AttributeError:
            pass
        if isinstance(component, Component) and not isinstance(component, Calendar):
            cal = Calendar()
            cal.add_component(component)
            component = cal
        return component

    def _validate_and_normalize_component(
        self, component: Union["Calendar", "Component", "CalendarObjectResource"]
    ) -> list["Component"]:
        """This method serves two purposes:

        1) Be liberal in what "component" it accepts and return
        something well-defined.  For instance, coponent may be a
        wrapped object (caldav.Event), an icalendar.Calendar or an
        icalendar.Event.  The return value will always be a list of
        icalendar components (i.e. Event), and Timezone components will
        be removed.

        2) Do some verification that the "component" is as expected
        and raise a ValueError if not.  The "component" should either
        be one single component or a recurrence set.  A recurrence set
        should conform to those rules:

        2.1) All components in the recurrence set should have the same UID

        2.2) First element ("master") of the recurrence set should have the RRULE
        property set

        2.3) Any following elements of a recurrence set ("exception
        recurrences") should have the RECURRENCE-ID property set.

        2.4) (there are more properties that may only be set in the
        master or only in the recurrences, but currently we don't do
        more checking than this)

        As for now, we do not support component to be a generator or a
        list, and things will blow up if component.subcomponents is a
        generator yielding infinite or too many subcomponents.

        """

        component = self._unwrap(component)
        components = [x for x in component.subcomponents if not isinstance(x, Timezone)]

        ## We shouldn't get here.  There should always be a valid component.
        if not len(components):
            raise ValueError("Empty component?")
        first = components[0]

        ## A recurrence set should always be one "master" with
        ## rrule-id set, followed by zero or more objects without
        ## rrule-id but with recurrence-id set
        if len(components) > 1:
            if (
                "rrule" not in components[0]
                or not all("recurrence-id" in x for x in components[1:])
                or any("rrule" in x for x in components[1:])
            ):
                raise ValueError(
                    "Expected a valid recurrence set, with one master component followed with special recurrences"
                )

        ## components should typically be a list with only one component.
        ## if there are more components, it should be a recurrence set
        ## one of the things identifying a recurrence set is that the
        ## uid is the same for all components in the set
        if any(x for x in components if x["uid"] != first["uid"]):
            raise ValueError(
                "Input parameter component is supposed to contain a single component or a recurrence set - but multiple UIDs found"
            )
        return components

    def _check_range(self, component: Component) -> bool:
        """Check if a component falls within the time range specified by self.start and self.end.

        Implements RFC4791 section 9.9 time-range filtering logic for VEVENT, VTODO, and VJOURNAL.

        :param component: A single calendar component (VEVENT, VTODO, or VJOURNAL)
        :return: True if the component matches the time range, False otherwise
        """
        comp_name = component.name

        ## The logic below should correspond neatly with RFC4791 section 9.9

        ## fetch comp_end and comp_start
        ## note that comp_end is DTSTART + DURATION if DURATION is given.
        ## note that for tasks, comp_end is set to DUE
        ## This logic is all handled by the start/end properties in the
        ## icalendar library, and makes the logic here less complex

        try:
            comp_end = _normalize_dt(component.end)
        except error.IncompleteComponent:
            comp_end = None

        try:
            comp_start = _normalize_dt(component.start)
        except error.IncompleteComponent:
            if component.name == "VEVENT":
                ## for events, DTSTART is mandatory
                raise
            comp_start = None

        if comp_name == "VEVENT":
            ## comp_start is always set.
            if not comp_end and isinstance(comp_start, datetime):
                ## if comp_end is not set and comp_start is a datetime,
                ## consider zero duration
                comp_end = comp_start
            elif not comp_end:
                ## if comp_end is not set and comp_start is a datetime,
                ## consider one day duration
                comp_end = comp_start + timedelta(day=1)
                ## TODO: What time of the day does the day change?
                ## Time zones are difficult!  TODO: as for now,
                ## self.start is a datetime, but in the future dates
                ## should be allowed as well.  Then the time zone
                ## problem for full-day events is at least simplified.

        elif comp_name == "VTODO":
            ## There is a long matrix for VTODO in the RFC, and it
            ## may seem complicated, but it isn't that bad:

            ## * A task with DTSTART and DURATION is equivalent with a
            ##   task with DTSTART and DUE.  This complexity is
            ##   already handled by the icalendar library, so all rows
            ##   in the matrix where VTODO has the DURATION property?"
            ##   is Y may be removed.
            ##
            ## * If either DUE or DTSTART is set, use it.
            if comp_end and not comp_start:
                comp_start = comp_end
            if comp_start and not comp_end:
                comp_end = comp_start

            ## * If both created/completed is set and
            ##   comp_start/comp_end is not set, then use those instead
            if not comp_start:
                if "CREATED" in component:
                    comp_start = _normalize_dt(component["CREATED"].dt)
                if "COMPLETED" in component:
                    comp_end = _normalize_dt(component["COMPLETED"].dt)

            ## * A task may have a DUE before the DTSTART.  The
            ##   complicated OR-logic in the table may be eliminated
            ##   by swapping start/end if necessary:
            if comp_end and comp_start and comp_end < comp_start:
                tmp = comp_start
                comp_start = comp_end
                comp_end = tmp

            ## * A task with no timestamps is considered to be done "at any or all days".
            if not comp_end and not comp_start:
                comp_start = _normalize_dt(DATE_MIN_DT)
                comp_end = _normalize_dt(DATE_MAX_DT)

        elif comp_name == "VJOURNAL":
            if not comp_start:
                ## Journal without DTSTART doesn't match time ranges
                return False
            if isinstance(comp_start, datetime):
                comp_end = comp_start
            else:
                comp_end = comp_start + timedelta(days=1)

        if comp_start == comp_end:
            ## Now the match requirement is start <= comp_end
            ## while otherwise the match requirement is start < comp_end
            ## minor detail, we'll work around it:
            comp_end += timedelta(seconds=1)

        ## After the logic above, all rows in the matrix boils down to
        ## this: (we could reduce it even more by defaulting
        ## self.start and self.end to DATE_MIN_DT etc)
        if self.start and self.end and comp_end:
            return self.start < comp_end and self.end > comp_start
        elif self.end:
            return self.end > comp_start
        elif self.start and comp_end:
            return self.start < comp_end
        return True

    def _check_completed_filter(self, component: Component) -> bool:
        """Check if a component should be included based on the include_completed filter.

        :param component: A single calendar component
        :return: True if the component should be included, False if it should be filtered out
        """
        if self.include_completed:
            return True

        ## If include_completed is False, exclude completed VTODOs
        ## Include everything that is not a VTODO, or VTODOs that are not completed
        return component.name != "VTODO" or (
            component.get("STATUS", "NEEDS-ACTION") == "NEEDS-ACTION"
            and "COMPLETED" not in component
        )

    def _expand_recurrences(
        self, recurrence_set: list[Component], comptypesu: set[str]
    ) -> Iterable[Component]:
        """Expand recurring events within the searcher's time range.

        Ensures expanded occurrences comply with RFC 5545:
        - Each occurrence has RECURRENCE-ID set
        - Each occurrence does NOT have RRULE (RRULE and RECURRENCE-ID are mutually exclusive)

        :param recurrence_set: List of calendar components to expand
        :param comptypesu: Set of component type strings (e.g., {"VEVENT", "VTODO"})
        :return: Iterable of expanded component instances
        """
        cal = Calendar()
        for x in recurrence_set:
            cal.add_component(x)
        recur = recurring_ical_events.of(cal, components=comptypesu)
        if not self.start:
            self.start = _normalize_dt(DATE_MIN_DT)
        if not self.end:
            self.end = _normalize_dt(DATE_MAX_DT)

        return recur.between(self.start, self.end)

    ## DISCLAIMER: AI-generated code.  But LGTM!
    def _check_property_filters(self, component: Component) -> bool:
        """Check if a component matches all property filters.

        :param component: A single calendar component
        :return: True if the component matches all property filters, False otherwise
        """
        for key, operator in self._property_operator.items():
            if operator == "undef":
                ## Property should NOT be defined
                if key in component:
                    return False
            elif operator == "contains":
                ## Property should contain the filter value (substring match)
                if key not in component:
                    return False
                comp_value = component[key]
                filter_value = self._property_filters[key]
                ## Convert to string for substring matching
                comp_str = str(comp_value)
                filter_str = str(filter_value)
                if filter_str.lower() not in comp_str.lower():
                    return False
            elif operator == "==":
                ## Property should exactly match the filter value
                if key not in component:
                    return False
                comp_value = component[key]
                filter_value = self._property_filters[key]
                ## Compare the values
                if comp_value != filter_value:
                    return False
            else:
                ## This shouldn't happen as add_property_filter validates operators
                raise NotImplementedError(f"Operator {operator} not implemented")

        return True

    ## DISCLAIMER: Mostly AI-generated code.  Alarms are a bit complex.
    ## I've done a little bit of polishing.  I still feel it should
    ## be possible to reduce some code duplication
    def _check_alarm_range(self, component: Component) -> bool:
        """Check if a component has alarms that fire within the alarm time range.

        Implements RFC 4791 section 9.9 alarm time-range filtering.

        :param component: A single calendar component (VEVENT, VTODO, or VJOURNAL)
        :return: True if any alarm fires within the alarm range, False otherwise
        """
        from datetime import timedelta

        ## Get all VALARM subcomponents
        alarms = [x for x in component.subcomponents if x.name == "VALARM"]

        if not alarms:
            ## No alarms - doesn't match alarm search
            return False

        ## Get component start/end for relative trigger calculations
        ## Use try/except because .start/.end may raise IncompleteComponent
        ## For VTODO, RFC 5545 says TRIGGER is relative to DUE if present, else DTSTART
        comp_start = None
        comp_end = None
        try:
            comp_start = _normalize_dt(component.start)
        except error.IncompleteComponent:
            pass
        try:
            comp_end = _normalize_dt(component.end)
        except error.IncompleteComponent:
            pass

        ## For each alarm, calculate when it fires
        for alarm in alarms:
            if "TRIGGER" not in alarm:
                continue

            trigger = alarm["TRIGGER"]

            ## The icalendar library stores trigger values in .dt attribute
            ## which can be either datetime (absolute) or timedelta (relative)
            if not hasattr(trigger, "dt"):
                continue

            trigger_value = trigger.dt

            ## Check if trigger is absolute (datetime) or relative (timedelta)
            if isinstance(trigger_value, timedelta):
                ## Relative trigger - timedelta from start or end
                trigger_delta = trigger_value

                ## Check TRIGGER's RELATED parameter (default is START)
                ## For VTODO, default anchor is DUE if present, else DTSTART
                related = "START"  # Default per RFC 5545
                if hasattr(trigger, "params") and "RELATED" in trigger.params:
                    related = trigger.params["RELATED"]

                ## Calculate alarm time based on RELATED and component type
                if related == "END" and comp_end:
                    alarm_time = comp_end + trigger_delta
                elif comp_start:
                    alarm_time = comp_start + trigger_delta
                else:
                    ## No start, end, or due to relate to
                    continue
            else:
                ## Absolute trigger - direct datetime
                alarm_time = _normalize_dt(trigger_value)

            ## Check for REPEAT and DURATION (repeating alarms/snooze functionality)
            ## Check all repetitions, not just the first alarm
            if "REPEAT" in alarm and "DURATION" in alarm:
                repeat_count = alarm["REPEAT"]
                duration = alarm["DURATION"].dt if hasattr(alarm["DURATION"], "dt") else None

                if duration:
                    ## Check each repetition
                    for i in range(int(repeat_count) + 1):
                        repeat_time = alarm_time + (duration * i)
                        ## Check if this repetition fires within the alarm range
                        if self.alarm_start and self.alarm_end:
                            if self.alarm_start <= repeat_time < self.alarm_end:
                                return True
                        elif self.alarm_start:
                            if repeat_time >= self.alarm_start:
                                return True
                        elif self.alarm_end:
                            if repeat_time < self.alarm_end:
                                return True
                    ## None of the repetitions matched
                    continue

            ## Check if this alarm (first occurrence) fires within the alarm range
            if self.alarm_start and self.alarm_end:
                if self.alarm_start <= alarm_time < self.alarm_end:
                    return True
            elif self.alarm_start:
                if alarm_time >= self.alarm_start:
                    return True
            elif self.alarm_end:
                if alarm_time < self.alarm_end:
                    return True

        return False
