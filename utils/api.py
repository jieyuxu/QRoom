from utils.database import Buildings, Rooms, Events, Groups, Users
from datetime import datetime, timedelta, time
from sqlalchemy import or_, and_
from flask_sqlalchemy_session import current_session
from pytz import timezone

sess = current_session

def current_dt():
    return datetime.now(timezone('US/Eastern')).replace(tzinfo=None)

def markPassed():
    current_time = current_dt()
    passed_events = sess.query(Events) \
                    .filter(Events.end_time < current_time) \
                    .filter(Events.passed == False) \
                    .all()

    for e in passed_events:
        e.passed = True

    sess.commit()

# find earliest event of the room that has not passed
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

# which time is later?
def isLater(current_time, start_time):
    if (start_time > current_time):
        return True
    return False

# taken from stack overflow
def inRange(start, end, time):
    # Return true if x is in the range [start, end]
    if start <= end:
        return start <= time <= end
    else:
        return start <= time or time <= end

# is this event when the group is available?
def isGroupOpen(group, event_time):
    start = group.open_time
    end = group.close_time

    x = time(event_time.hour, event_time.minute, event_time.second, 00)
    return inRange(start, end, x)

# get group associated with room
def getGroup(room):
    group_id = room.group_id
    group = sess.query(Groups)\
            .filter(Groups.group_id == group_id) \
            .first()

    return group

def isAvailable(room):
    group = getGroup(room)
    if isGroupOpen(group, current_dt()) == False:
        return False
    markPassed()
    existEvent, event = findEarliest(room)
    if not existEvent:
        return True

    return isLater(current_dt(), event.start_time)

# taken from stack overflow
def get30(date_time):
    return date_time + (datetime.min - date_time) % timedelta(minutes=30)

def add30(date_time):
    return date_time + timedelta(minutes=30)

# how many buttons to display?
def displayBookingButtons(room):
    FOUR_BUTTONS = 4
    ZERO_BUTTONS = 0

    markPassed()
    existEvent, event = findEarliest(room)

    group = getGroup(room)

    current_time = current_dt()

    if not isGroupOpen(group, current_time):
        print("not open")
        return ZERO_BUTTONS

    for i in range(4):
        if i == 0:
            time = get30(current_dt())
        else:
            time = add30(time)
        isOpen = isGroupOpen(group, time)
        if not isOpen:
            print("not open")
            return i
        if existEvent:
            # if time is later than the earliest events start time
            if isLater(event.start_time, time):
                print("later")
                return i

    return FOUR_BUTTONS

# how many buttons to display?
def displayExtendBookingButtons(room):
    FOUR_BUTTONS = 4
    ZERO_BUTTONS = 0

    markPassed()
    existEvent, event = findEarliest(room)

    group = getGroup(room)

    current_time = current_dt()

    if not isGroupOpen(group, current_time):
        return ZERO_BUTTONS

    time = get30(current_dt())
    for i in range(4):
        time = add30(time)
        isOpen = isGroupOpen(group, time)
        if not isOpen:
            return i
        if existEvent:
            # if time is later than the earliest events start time
            if isLater(event.start_time, time):
                print("later")
                return i

    return FOUR_BUTTONS


# has this user booked anything yet that has not passed
def hasBooked(user):
    markPassed()
    events = sess.query(Events) \
            .filter(Events.net_id == user.net_id) \
            .filter(Events.passed == False) \
            .all()

    if len(events) == 0:
        return False

    return True

# booking the room on the spot
def bookRoomAdHoc(user1, room, button_end_time):
    current_time = current_dt()

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

    event = Events(user = user1, event_title="AdHoc Booking", start_time = current_time,
                    end_time = button_end_time, room = room, passed = False)

    sess.add(event)
    sess.commit()

    return ''

# if user already exists, return user object
# else makes new user objects with admin = False, add to database,
# and returns new object
def getUser(net_id):
    user = sess.query(Users)\
            .filter(Users.net_id == net_id)\
            .first()

    if user is None:
        print("it tis none")
        user = Users(net_id= net_id, contact = net_id + '@princeton.edu', admin = False)
        sess.add(user)
        sess.commit()
    return user

# returns all events of a user, passed and unpassed
def getUserEvent(net_id):
    event = sess.query(Events)\
            .filter(Events.net_id == net_id)\
            .order_by(Events.start_time)\
            .all()
    return event

def isAdmin(user):
    print(type(user))
    return user.admin

def updateContact(user, contact):
    user.contact = contact

# helper for isAvailableScheduled; returns list of event objects that overlap with start_time, end_time for a room
def listAvailableScheduled(start_time, end_time, room):
    group = getGroup(room)

    if start_time > end_time:
        print('Start time later than end time')
        return 'Start time later than end time'

    if (not isGroupOpen(group, start_time)) or (not isGroupOpen(group, end_time)):
        print('Building is not open')
        return 'Building is not open'

    # shouldn't book an event that ends in the past
    current_time = current_dt()
    if (end_time < current_time):
        print('Event end time has passed')
        return 'Event end time has passed'

    conditions1 = []
    conditions1.append(Events.start_time <= start_time)
    conditions1.append(Events.end_time > start_time)
    clause1 = and_(*conditions1)

    conditions2 = []
    conditions2.append(Events.start_time >= start_time)
    conditions2.append(Events.start_time < end_time)
    clause2 = and_(*conditions2)

    clauses = [clause1, clause2]
    timeClause = or_(*clauses)

    # only display conflicts for the same room
    conditions3 = []
    conditions3.append(Events.room_id == room.room_id)
    conditions3.append(timeClause)
    combined = and_(*conditions3)

    events = sess.query(Events) \
            .filter(combined) \
            .all()
    print('Printing overlapping events')
    return events

# can you schedule it at these times in the future?
def isAvailableScheduled(start_time, end_time, room):
    # list of events that overlap
    print('entered is available scheduled, about to call list available scheduled')
    events = listAvailableScheduled(start_time, end_time, room)
    if (isinstance(events, str)):
        return events
    print('returned from list available scheduled')
    if len(events) != 0:
        message = 'The following events are scheduled during this time: \n'
        for e in events:
            message += '\n'
            message += str(e.event_title) + '\n'
            message += 'Booked By: ' + e.net_id + '\n'
            message += 'Start Time: ' + str(e.start_time) + '\n'
            message += 'End Time: ' + str(e.end_time) + '\n'

        return message

    return ''

def isAvailableScheduledEdit(start_time, end_time, room, current_event):
    # list of events that overlap
    events = listAvailableScheduled(start_time, end_time, room)

    seenConflictBefore = False
    message = ''
    if len(events) != 0:
        for e in events:
            if e.event_id != current_event.event_id:
                if not seenConflictBefore:
                    message = 'The following events are scheduled during this time: \n'
                    seenConflictBefore = True
                message += '\n'
                message += str(e.event_title) + '\n'
                message += 'Booked By: ' + e.net_id + '\n'
                message += 'Start Time: ' + str(e.start_time) + '\n'
                message += 'End Time: ' + str(e.end_time) + '\n'

    return message

# admin booking room for the future
def bookRoomSchedule(user, room, start_time, end_time, event_title = '<No Event Title>'):
    print('Entered book room schedule, about to call is available scheduled')
    if not isAdmin(user):
        return "NOT ADMIN"
    problem = isAvailableScheduled(start_time, end_time, room)
    print('returned from isAvailableScheduled')
    if problem != '':
        return problem
    event = Events(user = user, event_title= event_title, start_time = start_time,
                    end_time = end_time, room = room, passed = False)

    sess.add(event)
    sess.commit()
    return ""

# admin booking room for the future
def editRoomSchedule(user, room, start_time, end_time, current_event, event_title = '<No Event Title>'):
    if not isAdmin(user):
        return "NOT ADMIN"
    problem = isAvailableScheduledEdit(start_time, end_time, room, current_event)
    if problem != '':
        return problem
    # no problem -- release the current event booking and book a new one
    releaseEvent(current_event)
    print("Released current event")
    newEvent = Events(user = user, event_title= event_title, start_time = start_time,
                    end_time = end_time, room = room, passed = False)
    sess.add(newEvent)
    print("Added new (edited) event")
    sess.commit()
    return ""


def addAdmin(user, net_id):
    if not isAdmin(user):
        print ("not an admin")
        return "NOT ADMIN"
    new_user = getUser(net_id)
    new_user.admin = True
    sess.commit()
    return ""

def updateEvent(event, end_time):
    event.end_time = end_time;
    sess.commit()
    return ""

def releaseEvent(event):
    sess.delete(event)
    sess.commit()
    return ""

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
    events = sess.query(Events)\
            .filter(Events.room_id == room.room_id)\
            .all()
    return events

# get events given room object
def getEventsSorted(room):
    events = sess.query(Events)\
            .filter(Events.room_id == room.room_id)\
            .order_by(Events.start_time)\
            .all()
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
    print(building)
    room = sess.query(Rooms)\
                .filter(Rooms.room_name == room_name)\
                .filter(Rooms.building_id == building.building_id)\
                .first()
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
