# icalendar-searcher

This library should contain logic for searching, filtering and sorting icalendar data, as well as logic for storing and representing an icalendar search query.

## Audience

* This will be used for the python CalDAV client library, both for bundling search parameters together in one object and for doing client-side filtering when the server does not support the desired search query.
* This may be useful in any kind of software handling collections of calendar content and needing to do filtering or searches on it.
* This may also be useful by calendar server developers.

## Status as of v0.x.x

This library is full of stubbed implementations as for now.  The maintainer will urgently prioritize the bare minimum needed for refactoring the search functionality in the CalDAV library.  Version 1.0 may still contain some stubs, but should contain a relatively well-defined feature set.

## History

This is a spin-off from the python caldav project, started by Tobias Brox in 2025-11, the maintainer of the Python CalDAV client library at that time, in collaboration with the main contributors of the icalendar library.

## Performance

In the early versions, the filter method will take the calendar contents one by one and check if it matches or not.  This will work out well enough for small calendar sets.  If lots of searches are to be done on fairly static data (like what typically may happen at the server side in a calendaring system), then it would be an idea to add indexes.

## License

As for now I'm releasing this under the GNU Affero General Public License v.3.0.  If you find this too restrictive or if this causes license compatibility issues for you, please get in touch with me and I will consider to fix some dual licensing, like it's done with the python CalDAV library.

Any contributor has to accept that the code is released under AGPL v3.0 and at some point in the future may be dual-licensed under some more permissive license, like the EUPL v1.1.
