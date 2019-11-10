from app import Buildings, Rooms, Events, Groups, Users
from base import Session, engine, Base
from datetime import time, datetime
from api import *

# 2 - generate database schema


# 3 - create a new session
session = Session()

Base.metadata.drop_all(engine)
session.commit()

Base.metadata.create_all(engine)

#4 - populate database
firestone = Buildings(building_name = "Firestone")
frist = Buildings(building_name = "Frist")
lewis = Buildings(building_name = "Lewis")

group1 = Groups(open_time = time(0,00,00), close_time = time(18,00,00))
group2 = Groups(open_time = time(3,00,00), close_time = time(20,00,00))


room1 = Rooms(building = firestone, room_name = '101', group = group1)
room2 = Rooms(building = frist, room_name = '102', group = group2)
room3 = Rooms(building = lewis, room_name = '103', group = group1)
room4 = Rooms(building = firestone, room_name = '104', group = group1)

bob = Users(net_id= "bob", contact = 'bob@princeton.edu', admin = True)
paul = Users(net_id= "paul", contact = 'paul@princeton.edu', admin = False)

event1 = Events(user = bob, event_title="Bob's birthday",
start_time = datetime(2019, 11, 28, 23, 55, 59, 342380),
end_time = datetime(2019, 11, 29, 23, 55, 59, 0),
room = room1, passed = False)

# event2 = Events(user = bob, event_title="Bob's graduation",
# start_time = datetime(2020, 11, 28, 23, 55, 59, 342380),
# end_time = datetime(2020, 11, 29, 23, 55, 59, 0),
# room = room1, passed = False)
#
# event3 = Events(user = bob, event_title="Bob's nobel prize",
# start_time = datetime(2019, 11, 27, 23, 55, 59, 342380),
# end_time = datetime(2019, 11, 28, 23, 55, 59, 0),
# room = room1, passed = False)
#
# event4 = Events(user = bob, event_title="Bob's sweet 16",
# start_time = datetime(2019, 4, 28, 23, 55, 59, 342380),
# end_time = datetime(2019, 5, 29, 23, 55, 59, 0),
# room = room1, passed = False)
#
# event5 = Events(user = bob, event_title="Bob's prom",
# start_time = datetime(2019, 11, 8, 4, 0, 0, 0),
# end_time = datetime(2019, 11, 8, 5, 0, 0, 0),
# room = room1, passed = False)

session.add(firestone)
session.add(frist)
session.add(lewis)

session.add(group1)
session.add(group2)

session.add(room1)
session.add(room2)
session.add(room3)
session.add(room4)

session.add(bob)
session.add(paul)

session.add(event1)
# session.add(event2)
# session.add(event3)
# session.add(event4)
# session.add(event5)

session.commit()
# session.close()

# if __name__ == '__main__':
# findEarliest(room1)
# print(isLater(datetime(2019, 4, 29, 22, 55, 59, 342380), datetime(2019, 11, 29, 23, 55, 59, 0)))
# print(isGroupOpen(group1, datetime(2019, 4, 28, 23, 55, 59, 342380)))
# print(isAvailable(room1))
# print(displayBookingButtons(room1))
# print(hasBooked(bob))
# print(hasBooked(paul))
# print(getUser("bob"))
# print(getUser("bobby"))
# print(isAdmin(bob))
# updateContact(bob, "bbb@princeton.edu")
# session.commit()
# print(isAvailableScheduled(datetime(2019, 11, 10, 7, 0, 0, 0), datetime(2019, 11, 11, 15, 55, 59, 0), room1))
# print(addAdmin(bob, "pie"))
# bookRoomAdHoc(bob, room1, datetime(2019, 8, 28, 8, 55, 59, 342380), session)
# bookRoomAdHoc(bob, room1, datetime(2019, 8, 28, 23, 55, 59, 342380), session)
# session.commit()
# print(getBuildings())
# print(getRooms(firestone))
#
# session.delete(event1)
# session.commit()
# releaseEvent(event1, session)
bookRoomSchedule(bob, room1, datetime(2021, 8, 28, 5, 55, 59, 342380), datetime(2021, 8, 28, 8, 55, 59, 342380), session)
