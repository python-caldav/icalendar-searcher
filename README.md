# icalendar-searcher

This library should contain logic for searching, filtering and sorting icalendar data, as well as logic for storing and representing an icalendar search query.

## Audience

* This will be used for the python CalDAV client library, both for bundling search parameters together in one object, for doing client-side filtering when the server does not support the desired search query.
* This may be useful in any kind of software handling collections of calendar content and needing to do filtering or searches on it.
* This may also be useful by calendar server developers.

## Usage

No proper usage documentation has been written yet, sorry.  There are tons of inline comments and docstrings though.  The AI has contributed with quite some verbose comments in the test code, but little of it has been exposed to any proper QA.

## Related projects

* The project depends on the [icalendar](https://github.com/collective/icalendar) library, all calendar contents handled by this library is coming in and out as ``icalendar.Component`` or ``icalendar.Calendar``.  However, the library should also support wrapped objects (like instances of the ``caldav.Event`` class).
* The project depends on the [recurring-ical-events](https://github.com/niccokunzmann/python-recurring-ical-events) library for expanding recurrence sets.
* The project is used by the [Python CalDAV client library](https://github.com/python-caldav/caldav)

## Status as of v0.x.x

This library still has some stubbed implementations:

* While `searcher.check_component(component)` can check the search filters on one component (or recurrence set) and even expand recurring objects, the `searcher.filter()`-method is not yet implemented.  It should be a simple thing, it's just some design considerations on weather to support input/output as `icalendar.Calendar`-objects, wrapper objects from the CalDAV library, lists or whatever.
* Same goes with `searcher.sort()`.  There is implemented a `searcher.sorting_value(component)` though.
* Only operators supported so far is ==, contains and undef.  Other operators like !=/<>, <, <=, ~, etc has not been implemented.

As for now.  The maintainer will urgently prioritize the bare minimum needed for usage in the CalDAV library.

According to the SemVer rules, it's OK to still change the API in 0.x-versions, but the current API is likely to be quite stable.  There exist no changelog as for now, but it will be made prior to the 1.0-release.

## History

This is a spin-off from the python caldav project, started by Tobias Brox in 2025-11, the maintainer of the Python CalDAV client library at that time, in collaboration with the main contributors of the icalendar library.

## AI

The author has been experimenting a bit with AI usage while creating this project, both GitHub Copilot and Claude has been tested.  Most of the test code has been created by the AI.  AI has also been utilized a bit for refactoring, bug hunting, and a little bit code generation (particularly wrg of the collations support), but most of the "business logic" was written by me.

While all the AI-generated changes in the business logic has been looked through thoroughly, very little QA has been done on the test code.

## Performance

In the early versions, the filter method will take the calendar contents one by one and check if it matches or not.  This will work out well enough for small calendar sets.  If lots of searches are to be done on fairly static data (like what typically may happen at the server side in a calendaring system), then it would be an idea to add indexes.

The expansion part may cause millions of recurrences to be created.  It even supports open-ended intervals.  It's possible by returning generators.  However, things will most likely blow up and eat all the CPU and memory it gets the hands on whenever one wants to do sorting of such a thing.

## License

As for now I'm releasing this under the GNU Affero General Public License v.3.0.  If you find this too restrictive or if this causes license compatibility issues for you, I will consider to fix some dual licensing, like it's done with the python CalDAV library.

This also means that any contributor has to accept that the code is released under AGPL v3.0 and at some point in the future may be dual-licensed under some more permissive license, like the EUPL v1.1.

I don't have very strong opinions on licenses.  If you have any issues in one way or another, please reach out.
