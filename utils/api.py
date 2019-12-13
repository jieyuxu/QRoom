from utils.database import Buildings, Rooms, Events, Groups, Users
from datetime import datetime, timedelta, time
from sqlalchemy import or_, and_
from flask_sqlalchemy_session import current_session

sess = current_session

def markPassed():
    current_time = datetime.now()
    passed_events = sess.query(Events) \
                    .filter(Events.end_time < current_time) \
                    .filter(Events.passed == False) \
                    .all()

    for e in passed_events:
        e.passed = True

    sess.commit()

def findEarliest(room):
    markPassed()
    min_event = sess.query(Events) \
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
    x = time(event_time.hour, event_time.minute, event_time.second, 00)
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

# def isGroupOpen(group, event_time):
#     start = group.open_time
#     end = group.close_time
#     print(event_time.time())
#     print(start)
#     print(end)
#
#     return ((event_time.time() >= start) and (event_time.time() <= end))

def isAvailable(room):
    group = getGroup(room)
    if isGroupOpen(group, datetime.now()) == False:
        print('hi')
        return False
    markPassed()
    existEvent, event = findEarliest(room)
    if not existEvent:
        return True

    return isLater(datetime.now(), event.start_time)

def get30(date_time):
    # print("current date time:", date_time)
    # print("datetime.min - date_time", datetime.min - date_time)
    # print("timedelta", timedelta(minutes=delta))

    return date_time + (datetime.min - date_time) % timedelta(minutes=30)

def add30(date_time):
    return date_time + timedelta(minutes=30)

def getGroup(room):
    group_id = room.group_id
    group = sess.query(Groups)\
            .filter(Groups.group_id == group_id) \
            .first()

    return group

def displayBookingButtons(room):
    FOUR_BUTTONS = 4
    ZERO_BUTTONS = 0

    # mark events as passed
    markPassed()

    # find the next earliest event in room
    existEvent, event = findEarliest(room)

    # get the room's group
    group = getGroup(room)

    current_time = datetime.now()

    # if the room is not open, return buttons.
    if not isGroupOpen(group, current_time):
        return ZERO_BUTTONS

    # else,
    for i in range(4):
        # get the next 00 or 30 minute
        if i == 0:
            time = get30(datetime.now())
        else:
            time = add30(time)

        # make sure the room is open at this time
        isOpen = isGroupOpen(group, time)
        if not isOpen:
            return i
        # if there is a later event, make sure this time is before that start time.
        if existEvent:
            if isLater(event.start_time, time):
                return i

    return FOUR_BUTTONS

def hasBooked(user):
    markPassed()
    events = sess.query(Events) \
            .filter(Events.net_id == user.net_id) \
            .all()

    if len(events) == 0:
        return False

    return True

# def updateEvent(eventid, endtime):
#     event = getEventObject(eventid)
#     event
#
#

# if user already exists, return user object
# else makes new user objects with admin = False, add to database,
# and returns new object

def getUser(net_id):
    user = sess.query(Users)\
            .filter(Users.net_id == net_id)\
            .first()

    if user is None:
        print("it tis none")
        user = Users(net_id= net_id, contact = '', admin = True)
        sess.add(user)
        sess.commit()
    return user

def getUserEvent(net_id):
    event = sess.query(Events).filter(Events.net_id == net_id).first()
    return event

def isAdmin(user):
    print(type(user))
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

    events = sess.query(Events) \
            .filter(combined) \
            .all()

    if len(events) != 0:
        return False

    return True

def bookRoomSchedule(user, room, start_time, end_time, event_title = ''):
    if not isAdmin(user):
        return "NOT ADMIN"
    if not isAvailableScheduled(start_time, end_time, room):
        return "TIME NOT AVAILABLE"
    event = Events(user = user, event_title= event_title, start_time = start_time,
                    end_time = end_time, room = room, passed = False)

    sess.add(event)
    sess.commit()
    return ""

def addAdmin(user, net_id):
    if not isAdmin(user):
        return "NOT ADMIN"
    new_user = getUser(net_id)
    new_user.admin = True
    sess.commit()
    return ""

def releaseEvent(event):
    sess.delete(event)
    sess.commit()

def bookRoomAdHoc(user1, room, button_end_time):
    current_time = datetime.now()
    print(type(user1))
    if not isAdmin(user1) and hasBooked(user1):
        return "You have already booked a room at this time. Release previous room to book another one."
    if not isGroupOpen(getGroup(room), current_time):
        return "SYS FAILURE: Group not open at current time"
    if not isGroupOpen(getGroup(room), button_end_time):
        return "SYS FAILURE: Group not open at button end time"

    markPassed()
    existEvent, event = findEarliest(room)
    if existEvent and isLater(event.start_time, current_time):
        return "SYS FAILURE: current time later than start time of booked event"

    event = Events(user = user1, event_title="...", start_time = current_time,
                    end_time = button_end_time, room = room, passed = False)

    sess.add(event)
    sess.commit()

    return ''

# get list of building objects
def getBuildings():
    buildings = sess.query(Buildings).all()
    return buildings

def getLatLong(building):
    bldg = sess.query(Buildings)\
        .filter(Buildings.building_name == building).one()
    return bldg.latitude, bldg.longitude

# get rooms assos with building object, return dictionary with key = room and
# object = boolean for availability
def getRooms(building):
    rooms = sess.query(Rooms)\
            .filter(Rooms.building_id == building.building_id)\
            .all()
    dict = {}

    for r in rooms:
        dict[r] = isAvailable(r)

    return dict

# get events given room object
def getEvents(room):
    events = sess.query(Events).all()
    return events

# get assosiated building object from building name
def getBuildingObject(building_name):
    building = sess.query(Buildings)\
                .filter(Buildings.building_name == building_name)\
                .first()
    return building

# get associated room object from room name and building name
def getRoomObject(room_name, building_name):
    building = getBuildingObject(building_name)
    room = sess.query(Rooms)\
                .filter(Rooms.room_name == room_name)\
                .filter(Rooms.building_id == building.building_id)\
                .first()
    print(room)
    return room

# get associated event object given event_id
def getEventObject(event_id):
    event = sess.query(Events).filter(Events.event_id == event_id).first()
    return event

# get associated building name and room name from room_id
def getBuildingRoomName(room_id):
    room = sess.query(Rooms).filter(Rooms.room_id == room_id).first()
    roomname = room.room_name
    building = sess.query(Buildings).filter(Buildings.building_id == room.building_id).first()
    buildingname = building.building_name
    return [buildingname, roomname]

# gets user object from net id
def getUserObject(net_id):
    user = sess.query(Users)\
                .filter(Users.net_id == net_id)\
                .first()
    return user

def isOpen(start, end, time):
    return ((time >= start) and (time <= end))
