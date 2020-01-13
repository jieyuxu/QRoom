from utils.database import Buildings, Rooms, Events, Groups, Users
from utils.base import session_factory, engine, Base
from datetime import time, datetime
from utils.api import *

# 2 - generate database schema

# 3 - create a new session
print('made session')
Base.metadata.drop_all(engine)
print('dropped db')
print('commited stuff')

Base.metadata.create_all(engine)

# 4 - populate database
firestone = Buildings(building_name="Firestone Library",
                      latitude=40.3495742, longitude=-74.6596086)

frist = Buildings(building_name="Frist Campus Center",
                  latitude=40.3468512, longitude=-74.6574649)

lewis = Buildings(building_name="Lewis Library",
                  latitude=40.3461306, longitude=-74.654834)

philly = Buildings(building_name="Prof. Dondero's Home",
                   latitude=40.052526, longitude=-75.056786)

sherred = Buildings(building_name="Paul's Office", latitude=40.3496224, longitude=-74.6526984)
                   
# @40.3423081,-74.6596026

group1 = Groups(open_time=time(8, 00, 00), close_time=time(5, 00, 00))
group2 = Groups(open_time=time(8, 00, 00), close_time=time(20, 00, 00))

room1 = Rooms(building=firestone, room_name='101', group=group1)
room2 = Rooms(building=frist, room_name='102', group=group2)
room3 = Rooms(building=lewis, room_name='103', group=group1)
room4 = Rooms(building=firestone, room_name='104', group=group1)
room5 = Rooms(building=sherred, room_name='006', group=group2)

paul = Users(net_id="pe5", contact='pe5@princeton.edu', admin=True)
bob = Users(net_id="rdondero", contact='rdondero@princeton.edu', admin=True)

saishaa = Users(net_id="saishaa", contact="saisha@princton.edu", admin=True)
suki = Users(net_id="sukiy", contact="sukiy@princton.edu", admin=True)
amy = Users(net_id="jyxu", contact="jyxu@princton.edu", admin=True)
jeanna = Users(net_id="jmjoseph", contact="jmjoseph@princeton.edu", admin=True)

event1 = Events(user=paul, event_title="Paul's birthday",
                start_time=datetime(2020, 11, 28, 23, 55, 59, 342380),
                end_time=datetime(2020, 11, 29, 23, 55, 59, 0),
                room=room1, passed=False)

event2 = Events(user=saishaa, event_title="Graduation",
                start_time=datetime(2021, 6, 28, 23, 55, 59, 342380),
                end_time=datetime(2021, 6, 29, 23, 55, 59, 0),
                room=room3, passed=False)


event3 = Events(user=suki, event_title="QRoom Meeting",
                start_time=datetime(2020, 2, 1, 16, 00, 59, 342380),
                end_time=datetime(2020, 2, 1, 16, 55, 59, 0),
                room=room5, passed=False)


sess = session_factory()
sess.add(firestone)
sess.add(frist)
sess.add(lewis)
sess.add(philly)
sess.add(sherred)

sess.add(group1)
sess.add(group2)

sess.add(room1)
sess.add(room2)
sess.add(room3)
sess.add(room4)
sess.add(room5)

sess.add(paul)
sess.add(bob)
sess.add(saishaa)
sess.add(suki)
sess.add(amy)
sess.add(jeanna)

sess.add(event1)
sess.add(event2)
sess.add(event3)

sess.commit()
sess.close()
