from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/mydb'
db = SQLAlchemy(app)

# Create our database model
class Buildings(db.Model):
    __tablename__ = "buildings"

    building_id = db.Column(db.Integer, primary_key=True)
    building_name = db.Column(db.String(120), unique=True)

    # a building can be associated with more than 1 room
    rooms = db.relationship("Rooms")

    def __init__(self, name):
        self.building_name = name

class Rooms(db.Model):
    __tablename__= "rooms"

    room_id = db.Column(db.Integer, primary_key=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.building_id'))
    room_number = db.Column(db.Integer)
    group_id = db.Column(db.Integer)

    def __init__(self, building, number, group):
        self.building_id = building
        self.room_number = number
        self.group_id = group

class Events(db.Model):
    __tablename__ = "events"

    event_id = db.Column(db.Integer, primary_key=True)
    net_id = db.Column(db.String(120))
    event_title = db.Column(db.String(120))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    room_id = db.Column(db.Integer)
    passed = db.Column(db.Boolean)

    def __init__(self, net_id, event_title, start_time, end_time, room_id, passed):
        self.net_id = net_id
        self.event_title = event_title
        self.start_time = start_time
        self.end_time = end_time
        self.room_id = room_id
        self.passed = passed

class Hours(db.Model):
    __tablename__ = "hours"

    group_id = db.Column(db.Integer, primary_key=True)
    open_time = db.Column(db.Time)
    close_time = db.Column(db.Time)

    def __init__(self, open_time, close_time):
        self.open_time = open_time
        self.close_time = close_time

class Users(db.Model):
    __tablename__ = "users"

    net_id = db.Column(db.String(120), primary_key=True)
    contact = db.Column(db.String(120))
    admin = db.Column(db.Boolean)

    def __init__(self, net_id, contact, admin):
        self.net_id = net_id
        self.contact = contact
        self.admin = admin

if __name__ == '__main__':
    app.debug = True
    # app.run()
