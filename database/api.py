from app import Buildings, Rooms, Events, Groups, Users
from base import Session, engine, Base
from datetime import datetime, timedelta

session = Session()

def markPassed():
    current_time = datetime.now()
    passed_events = session.query(Events) \
                    .filter(Events.end_time < current_time) \
                    .filter(Events.passed == False) \
                    .all()

    for e in passed_events:
        e.passed = True

    session.commit()

def findEarliest(room):
    markPassed()
    min_event = session.query(Events) \
            .filter(Events.passed == False) \
            .filter(Events.room_id == room.room_id) \
            .order_by(Events.start_time) \
            .first()

    if (min_event is None):
        return False, min_event

    return True, min_event

def isLater(current_time, start_time):
    if (start_time > current_time):
        return True
    return False

def isGroupOpen(group, event_time):
    start = group.open_time
    end = group.close_time

    return ((event_time.time() >= start) and (event_time.time() <= end))

def isAvailable(room):
    markPassed()
    existEvent, event = findEarliest(room)
    if not existEvent:
        return True
    return isLater(datetime.now(), event.start_time)

def getDelta(date_time, delta):
    return date_time + (datetime.min - date_time) % timedelta(minutes=delta)

def getGroup(room):
    group_id = room.group_id
    group = session.query(Groups)\
            .filter(Groups.group_id == group_id) \
            .first()

    return group

def displayBookingButtons(room):
    FOUR_BUTTONS = 4
    ZERO_BUTTONS = 0
    THIRTY_MIN = 30

    markPassed()
    existEvent, event = findEarliest(room)

    group = getGroup(room)

    current_time = datetime.now()

    if not isGroupOpen(group, current_time):
        return ZERO_BUTTONS

    for i in range(4):
        time = getDelta(current_time, THIRTY_MIN + THIRTY_MIN * i)
        isOpen = isGroupOpen(group, time)
        if not isOpen:
            return i
        if existEvent:
            if isLater(event.start_time, time):
                return i

    return FOUR_BUTTONS

def hasBooked(user):
    markPassed()
    events = session.query(Events) \
            .filter(Events.net_id == user.net_id) \
            .all()

    if len(events) == 0:
        return False

    return True

# def releaseRoom(event):
#     session.delete(event)
#     session.commit()

def bookRoomAdHoc(user1, room, button_end_time):
    current_time = datetime.now()

    if not user1.admin and hasBooked(user):
        print("You have already booked a room at this time. Release previous room to book another one.")
    if not isGroupOpen(getGroup(room), current_time):
        print("SYS FAILURE")
    if not isGroupOpen(getGroup(room), button_end_time):
        print("SYS FAILURE")

    markPassed()
    existEvent, event = findEarliest(room)
    if existEvent and isLater(event.start_time, current_time):
        print("SYS FAILURE")

    event = Events(user = user1, event_title="...", start_time = current_time,
                    end_time = button_end_time, room = room, passed = False)

    session.add(event)
    session.commit()
