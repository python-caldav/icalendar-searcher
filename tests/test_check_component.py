from icalendar import Calendar, Todo, Event, Journal
from icalendar_searcher import Searcher
from datetime import datetime

def test_check_empty():
    searcher = Searcher(start=datetime(1970,1,1), end=datetime.now())
    
    ## TODO: icalendar7 (not released yet) has some
    ## factory methods for creating valid VCALENDAR
    ## objects (IIRC).
    empty_calendar = Calendar()

    ## An empty calendar should yield nothing (currently
    ## the docstring says it should return None, but [] is probably
    ## equally acceptable)
    assert not searcher.check_component(empty_calendar)

def test_filter_component_types():
    searcher = Searcher(todo=True)
    cal = Calendar()
    comp = Event()
    comp['uid'] = 'someuid'
    cal.add_component(comp)
    assert not searcher.check_component(cal)
