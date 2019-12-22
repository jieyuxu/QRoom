from utils.database import Buildings, Rooms, Events, Groups, Users
from utils.base import session_factory, engine, Base
from datetime import time, datetime
from utils.api import *

# 2 - generate database schema
# session = current_session
# print(session)
# session.close()
# 3 - create a new session
print('made session')
Base.metadata.drop_all(engine)
print('dropped db')
print('commited stuff')

Base.metadata.create_all(engine)

#4 - populate database
firestone = Buildings(building_name = "Firestone", latitude=40.3495742, longitude=-74.6596086)
frist = Buildings(building_name = "Frist", latitude=40.3468512, longitude=-74.6574649)
# lewis = Buildings(building_name = "Lewis", latitude=40.3461, longitude=74.6526)
lewis = Buildings(building_name = "Lewis", latitude=40.348833, longitude=-74.6550017)
shepperd = Buildings(building_name = "Sherrerd Hall", latitude=40.3495354, longitude=-74.654877)
friend = Buildings(building_name = "Friend Center", latitude=40.3505495, longitude=-74.6543927)
# @40.3423081,-74.6596026

group1 = Groups(open_time = time(8,00,00), close_time = time(4,00,00))
group2 = Groups(open_time = time(8,00,00), close_time = time(20,00,00))


room1 = Rooms(building = firestone, room_name = '101', group = group1)
room2 = Rooms(building = frist, room_name = '102', group = group2)
room3 = Rooms(building = lewis, room_name = '103', group = group1)
room4 = Rooms(building = firestone, room_name = '104', group = group1)
room5 = Rooms(building = shepperd, room_name = '3rd Floor Atrium', group = group1)
room6 = Rooms(building = friend, room_name = '006', group = group2)

bob = Users(net_id= "bob", contact = 'bob@princeton.edu', admin = True)
paul = Users(net_id= "paul", contact = 'paul@princeton.edu', admin = False)
saishaa = Users(net_id= "saishaa", contact="saisha@princton.edu", admin = True)
suki = Users(net_id= "sukiy", contact="sukiy@princton.edu", admin = True)

event1 = Events(user = bob, event_title="Bob's birthday",
start_time = datetime(2020, 11, 28, 23, 55, 59, 342380),
end_time = datetime(2020, 11, 29, 23, 55, 59, 0),
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

sess = session_factory()
sess.add(firestone)
sess.add(frist)
sess.add(lewis)

sess.add(group1)
sess.add(group2)

sess.add(room1)
sess.add(room2)
sess.add(room3)
sess.add(room4)

sess.add(bob)
sess.add(paul)
sess.add(saishaa)
sess.add(suki)

sess.add(event1)
# sess.add(event2)
# sess.add(event3)
# sess.add(event4)
# sess.add(event5)

sess.commit()
# sess.close()

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
# sess.commit()
# print(isAvailableScheduled(datetime(2019, 11, 10, 7, 0, 0, 0), datetime(2019, 11, 11, 15, 55, 59, 0), room1))
# print(addAdmin(bob, "pie"))
# bookRoomAdHoc(bob, room1, datetime(2019, 8, 28, 8, 55, 59, 342380), sess)
# bookRoomAdHoc(bob, room1, datetime(2019, 8, 28, 23, 55, 59, 342380), sess)
# sess.commit()
# print(getBuildings())
# print(getBuildingObject("Firestone"))
# firestone = Buildings(building_name = "Firestone")
# print(getRooms(firestone))
# print(datetime(2021, 8, 28, 5, 55, 59, 342380))
# print(int('05'))
#
# sess.delete(event1)
# sess.commit()
# releaseEvent(event1, sess)
# bookRoomSchedule(bob, room1, datetime(2021, 8, 28, 5, 55, 59, 342380), datetime(2021, 8, 28, 8, 55, 59, 342380))
sess.close()
