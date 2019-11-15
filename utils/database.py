from sqlalchemy import Column, String, Integer, DateTime, Time, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

# Create our database model
class Buildings(Base):
    __tablename__ = "buildings"

    building_id = Column(Integer, primary_key=True)
    building_name = Column(String(120), unique=True)

    # a building can be associated with more than 1 room
    rooms = relationship("Rooms", backref='building')


class Rooms(Base):
    __tablename__= "rooms"

    room_id = Column(Integer, primary_key=True)
    building_id = Column(Integer, ForeignKey('buildings.building_id'), nullable=False)
    room_name = Column(String(120), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.group_id'), nullable=False)

    events = relationship("Events", backref='room')


class Events(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True)
    net_id = Column(String(120), ForeignKey('users.net_id'), nullable=False)
    event_title = Column(String(120), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.room_id'), nullable=False)
    passed = Column(Boolean, nullable=False)

    users = relationship("Users")


class Groups(Base):
    __tablename__ = "groups"

    group_id = Column(Integer, primary_key=True)
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)

    rooms = relationship("Rooms", backref='group')


class Users(Base):
    __tablename__ = "users"

    net_id = Column(String(120), primary_key=True)
    contact = Column(String(120), nullable=True)
    admin = Column(Boolean, nullable=False)

    events = relationship("Events", backref='user')
