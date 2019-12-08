from utils.database import Buildings, Rooms, Events, Groups, Users
from datetime import datetime, timedelta, time, date
from sqlalchemy import or_, and_
from flask_sqlalchemy_session import current_session
from pytz import timezone

sess = current_session

# pieces from https://stackoverflow.com/questions/16603645/how-to-convert-datetime-time-from-utc-to-different-timezone
# second parameter is what it should convert to, if not utc then auto est
# time must not be naive
def time_to_timezone(t, zone):
    if zone.lower() is 'utc':
        tzone = timezone('UTC')
    else:
        tzone = timezone('US/Eastern')

    dt = datetime.combine(date.today(), t)
    new_dt = dt.astimezone(tzone)
    return new_dt.time()

# assumes est input
# second parameter is what it should convert to, if not utc then auto est
# time must not be naive
def datetime_to_timezone(dt, zone):
    if zone.lower() == 'utc':
        tzone = timezone('UTC')
    else:
        tzone = timezone('US/Eastern')

    new_time = dt.astimezone(tzone)
    return new_time

# gets naive time of current time
def datetime_now():
    now = datetime.now(timezone('UTC'));
    return now.replace(tzinfo=None)

# updates table to marked passed events passed
def markPassed():
    current_time = datetime_now()
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
def isOpen(start, end, time):
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

    return isOpen(start, end, x)

# is this room available right now?
def isAvailable(room):
    group = getGroup(room)
    if isGroupOpen(group, datetime_now()) == False:
        return False
    markPassed()
    existEvent, event = findEarliest(room)
    if not existEvent:
        return True

    return isLater(datetime_now(), event.start_time)

# taken from stack overflow
def get30(date_time):
    return date_time + (datetime.min - date_time) % timedelta(minutes=30)

def add30(date_time):
    return date_time + timedelta(minutes=30)

# get group associated with room
def getGroup(room):
    group_id = room.group_id
    group = sess.query(Groups)\
            .filter(Groups.group_id == group_id) \
            .first()

    return group

# how many buttons to display?
def displayBookingButtons(room):
    FOUR_BUTTONS = 4
    ZERO_BUTTONS = 0

    markPassed()
    existEvent, event = findEarliest(room)

    group = getGroup(room)

    current_time = datetime_now()

    if not isGroupOpen(group, current_time):
        return ZERO_BUTTONS

    for i in range(4):
        if i == 0:
            time = get30(datetime_now())
        else:
            time = add30(time)
        isOpen = isGroupOpen(group, time)
        if not isOpen:
            return i
        if existEvent:
            if isLater(event.start_time, time):
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
    current_time = datetime_now()
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

# returns all events of a user, passed and unpassed
def getUserEvent(net_id):
    event = sess.query(Events).filter(Events.net_id == net_id).all()
    return event

def isAdmin(user):
    print(type(user))
    return user.admin

def updateContact(user, contact):
    user.contact = contact

# can you schedule it at these times in the future?
def isAvailableScheduled(start_time, end_time, room):
    group = getGroup(room)

    if (not isGroupOpen(group, start_time)) or (not isGroupOpen(group, end_time)):
        return False

    # shouldn't book an event that ends in the past
    current_time = datetime_now()
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

# admin booking room for the future
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

def str_to_datetime(time):
    year = int(time[0:4])
    month = int(time[5:7])
    day = int(time[8:10])
    hour = int(time[11:13])
    minute = int(time[14:16])
    return datetime(year, month, day, hour, minute, 0, 0)
