from database import Buildings, Rooms, Events, Groups, Users
from base import Session, engine, Base
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

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

# if user already exists, return user object
# else makes new user objects with admin = False, add to database,
# and returns new object

def getUser(net_id):
    user = session.query(Users)\
            .filter(Users.net_id == net_id)\
            .first()

    if user is None:
        user = Users(net_id= net_id, contact = '', admin = False)
        session.add(user)
        session.commit()

    return user

def isAdmin(user):
    return user.admin

def updateContact(user, contact):
    user.contact = contact

def isAvailableScheduled(start_time, end_time, room):
    group = getGroup(room)

    if (not isGroupOpen(group, start_time)) or (not isGroupOpen(group, end_time)):
        return False

    # shouldn't book an event that ends in the past
    current_time = datetime.now()
    if (end_time < current_time):
        return False

    conditions1 = []
    conditions1.append(Events.start_time < start_time)
    conditions1.append(Events.end_time > start_time)
    clause1 = and_(*conditions1)

    conditions2 = []
    conditions2.append(Events.start_time > start_time)
    conditions2.append(Events.start_time < end_time)
    clause2 = and_(*conditions2)

    clauses = [clause1, clause2]
    combined = or_(*clauses)

    events = session.query(Events) \
            .filter(combined) \
            .all()

    if len(events) != 0:
        return False

    return True

def bookRoomSchedule(user, room, start_time, end_time, session, event_title = ''):
    if not isAdmin(user):
        return "NOT ADMIN"
    if not isAvailableScheduled(start_time, end_time, room):
        return "TIME NOT AVAILABLE"
    event = Events(user = user, event_title= event_title, start_time = start_time,
                    end_time = end_time, room = room, passed = False)

    session.add(event)
    session.commit()
    return ""

def addAdmin(user, net_id):
    if not isAdmin(user):
        return "NOT ADMIN"
    new_user = getUser(net_id)
    new_user.admin = True
    session.commit()
    return ""

def releaseEvent(event, session):
    session.delete(event)
    session.commit()

def bookRoomAdHoc(user1, room, button_end_time, session):
    current_time = datetime.now()

    if not user1.admin and hasBooked(user):
        print("You have already booked a room at this time. Release previous room to book another one.")
    if not isGroupOpen(getGroup(room), current_time):
        print("SYS FAILURE: Group not open at current time")
    if not isGroupOpen(getGroup(room), button_end_time):
        print("SYS FAILURE: Group not open at button end time")

    markPassed()
    existEvent, event = findEarliest(room)
    if existEvent and isLater(event.start_time, current_time):
        print("SYS FAILURE: current time later than start time")

    event = Events(user = user1, event_title="...", start_time = current_time,
                    end_time = button_end_time, room = room, passed = False)

    session.add(event)
    session.commit()

# get list of building objects
def getBuildings():
    buildings = session.query(Buildings).all()
    return buildings

# get rooms assos with building object, return dictionary with key = room and
# object = boolean for availability
def getRooms(building):
    rooms = session.query(Rooms)\
            .filter(Rooms.building_id == building.building_id)\
            .all()
    dict = {}
    for r in rooms:
        dict[r] = isAvailable(r)

    return dict

# get events given room object
def getEvents(room):
    events = session.query(Events).all()
    return events

# get assosiated building object from building name
def getBuildingObject(building_name):
    building = session.query(Buildings)\
                .filter(Buildings.building_name == building_name)\
                .first()
    return building

# get associated room object from room name and building name
def getRoomObject(room_name, building_name):
    building = getBuildingObject(building_name)
    room = session.query(Rooms)\
                .filter(Rooms.room_name == room_name)\
                .filter(Rooms.building_id == building.building_id)\
                .first()
    return room

session.close()
