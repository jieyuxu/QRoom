from flask import Flask, request, render_template, url_for, redirect, current_app
from flask import session
import os
from utils.api import *
from flask_sqlalchemy_session import flask_scoped_session
from utils.base import session_factory
from distance import distance
from CAS import CAS
from CAS import login_required
from pywebpush import webpush, WebPushException
from flask_mail import Message, Mail
import smtplib
#import threading


app = Flask(__name__)
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'qroomteam@gmail.com'
app.config['MAIL_PASSWORD'] = 'WeLoveBob123'

mail = Mail(app)



app.secret_key = 'hello its me'
# print(os.random(24))
sess = flask_scoped_session(session_factory, app)

########## CAS AUTHENTICATION ###########
cas = CAS(app)
app.config['CAS_SERVER'] = "https://fed.princeton.edu/cas/login"
app.config['CAS_AFTER_LOGIN'] = 'caslogin'
# app.config['CAS_AFTER_LOGOUT'] = 'http://princeton-qroom.herokuapp.com/caslogout'
app.config['CAS_AFTER_LOGOUT'] = 'localhost:5000/caslogout'
app.config['CAS_LOGIN_ROUTE'] = '/cas'
#########################################

@app.route('/')
def index():
   if isLoggedIn():
      return redirect(url_for('profile'))
      session['admin'] = True

   return render_template("index.html",loggedin = isLoggedIn(), admin = False)

@app.route('/caslogin')
def caslogin():
   print(app.config['CAS_USERNAME_SESSION_KEY'])
   if cas.username is not None:
      print("user:", cas.username)
      session['username'] = cas.username
      print("confirming user logged into session", session['username'])
      session.modified = True
      # add user to database if not in there
      # returns user object that was added
      user = getUser(str(cas.username))
      if isAdmin(user):
         session['admin'] = cas.username
         print('i got here')
   return redirect(url_for('profile'))

@app.route('/caslogout')
def caslogout():
   if isLoggedIn():
      session.pop('username')
      if 'admin' in session:
          session.pop('admin')
      session.modified = True
   return redirect(url_for('index'))

@app.route('/profile')
def profile():
   if isLoggedIn():
      event = getUserEvent(session['username'])
      eventDetails = {}
      buildingname=''
      roomname=''
      eventid=''
      if event is not None:
         eventDetails['Start Time'] = event.start_time
         eventDetails['End Time'] = event.end_time
         room = getBuildingRoomName(event.room_id)
         buildingname = room[0]
         roomname = room[1]
         eventid = event.event_id

      if 'admin' in session:
         return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username,
                                 event=eventDetails, eventid=eventid, building=buildingname, room=roomname, admin = True)
      else:
         return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username,
                                 event=eventDetails, eventid=eventid, building=buildingname, room=roomname, admin = False)
   else:
      return redirect(url_for("index"))

@app.route('/buildings', methods=['GET', 'POST'])
def buildings():
    if isLoggedIn():
        buildings_query = getBuildings()
        buildings = []
        for b in buildings_query:
            buildings.append(b.building_name)
        if 'admin' in session:
           return render_template("buildings.html", loggedin = isLoggedIn(), username = cas.username, buildings=buildings, admin = True)
        else:
           return render_template("buildings.html", loggedin = isLoggedIn(), username = cas.username, buildings=buildings, admin = False)
    else:
      return redirect(url_for("index"))

@app.route('/rooms', methods=['GET', 'POST'])
def rooms():
    if isLoggedIn():
        building = str(request.args.get('building'))
        building_object = getBuildingObject(building)

        # returns a dictionary of keys = rooms, objects = availability
        rooms_query = getRooms(building_object)
        rooms = {}
        for r in rooms_query.keys():
           rooms[r.room_name] = rooms_query[r]
        if 'admin' in session:
           return render_template("rooms.html", loggedin = isLoggedIn(), username = cas.username,
                                    building=building, rooms=rooms, admin = True)
        else:
           return render_template("rooms.html", loggedin = isLoggedIn(), username = cas.username,
                                    building=building, rooms=rooms, admin = False)
    else:
       return redirect(url_for("index"))

@app.route('/checkcoordinates', methods=['GET', 'POST'])
def checkCoordinates():
   print("received request")
   if isLoggedIn() and request.method == 'POST':
      if request.is_json:
         content = request.get_json()
         userLat = content['latitude']
         userLong = content['longitude']
         building = content['building']

         bldgLat, bldgLong = getLatLong(building)
         dist = distance(userLat, bldgLat, userLong, bldgLong)
         if dist > 0.2:
            return "You are too far away from " + building + " to book a room. You must be within 200 meters of a building to book a room."
         # code to confirm location
         return ""


@app.route('/bookRoom', methods=['GET', 'POST'])
def bookRoom():
   THIRTY_MIN = 30

   loggedin = False
   if 'username' in session:
      loggedin = True
      building = request.args.get('building')
      room = str(request.args.get('room'))
      room_object = getRoomObject(room, building)
      number = displayBookingButtons(room_object) # number of buttons to display
      times = []
      fullTimes = [] # military time
      for i in range(number):
         if i == 0:
            time = get30(datetime.now())
         else:
            time = add30(time)
         times.append(str(time)[11:16])
         fullTimes.append(str(time))
      print(times)
      print(fullTimes)
      if 'admin' in session:
         return render_template("bookRoom.html", loggedin = loggedin, username = cas.username, building=building, room=room, times = times, fullTimes = fullTimes, admin = True)
      else:
         return render_template("bookRoom.html", loggedin = loggedin, username = cas.username, building=building, room=room, times = times, fullTimes = fullTimes, admin = False)

   else:
      return redirect(url_for("index"))

@app.route('/viewRoom', methods=['GET', 'POST'])
def viewRoom():
   if isLoggedIn():
      building = request.args.get('building')
      room = request.args.get('room')
      print('building: ', building)
      print('room ', room)
      # get current time and get delta 30
      # get until 0:00
      time = get30(datetime.now())
      # get all events in room for a certain day
      events = getEvents(getRoomObject(room, building))
      print('printing all events')
      print(events)
      times_blocked = []
      dictionary = {}
      count = 0
      for e in events:
         print (count)
         # print("hi " + str(e))
         print("curr object", e)
         times_blocked.append([e.start_time, e.end_time])
         count = count + 1
      while time.hour != 0:
         for t in times_blocked:
            dictionary[time] = isOpen(t[0], t[1], time)
         time = add30(time)

      isAvailable = False
      length = len(dictionary)
      if 'admin' in session:
         return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, times = dictionary, isAvailable = isAvailable, length = length, admin = True)
      else:
         return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, times = dictionary, isAvailable = isAvailable, length = length, admin = False)
   else:
      return redirect(url_for("index"))

@app.route('/confirmation', methods=['GET', 'POST'])
def confirmation():
    if isLoggedIn():
        building = request.args.get('building')
        room = request.args.get('room')
        # assuming time is a string form of datetime object, like '2021-08-28 05:55:59.342380'
        time = str(request.args.get('fullTime'))
        print("THIS IS THE TIME", time)
        # assuming 'username' means netid
        user = getUser(cas.username)
        print("THIS IS THE USER", user)
        room_object = getRoomObject(room, building)
        year = int(time[0:4])
        month = int(time[5:7])
        day = int(time[8:10])
        hour = int(time[11:13])
        minute = int(time[14:16])
        end_time = datetime(year, month, day, hour, minute, 0, 0)

        # updates database, returns empty string if successful
        print("username:" + cas.username)
        print("confirmation" + str(type(user)))
        error = bookRoomAdHoc(user, room_object, end_time)

        if 'admin' in session:
           return render_template("confirmation.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], fullTime = time, admin = True)
        else:
           return render_template("confirmation.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], fullTime = time, admin = False)
    else:
      return redirect(url_for("index"))

@app.route('/releaseRoom', methods=['GET','DELETE'])
def releaseRoom():
   if isLoggedIn():
      eventid = request.args.get('eventid')
      buildingname = request.args.get('building')
      roomname = request.args.get('room')
      event = getEventObject(eventid)
      releaseEvent(event)

      if 'admin' in session:
         return render_template("releaseRoom.html", loggedin = isLoggedIn(), username = cas.username, building=buildingname, room=roomname, admin = True)
      else:
         return render_template("releaseRoom.html", loggedin = isLoggedIn(), username = cas.username, building=buildingname, room=roomname, admin = False)
   else:
      return redirect(url_for("index"))

@app.route('/admin', methods = ['GET', 'POST'])
def admin():
   if isLoggedIn():
      # query buildings for the admin template
      buildings_query = getBuildings()
      buildings = []
      for b in buildings_query:
         buildings.append(b.building_name)
      print(buildings)

      addMessage = ""
      if 'addMessage' in request.args:
         addMessage = request.args.get('addMessage')

      bookMessage = ""
      if 'bookMessage' in request.args:
         bookMessage = request.args.get('bookMessage')

      bookFlag = False
      addFlag = False
      if 'bookFlag' in request.args:
         bookFlag = request.args.get('bookFlag')
      if 'addFlag' in request.args:
         print("request.args found an AddFlag")
         addFlag = request.args.get('addFlag')
         print("addflag", addFlag)

      return render_template("admin.html", loggedin = isLoggedIn(), username = cas.username, admin = isAdmin, addMessage = addMessage, bookMessage = bookMessage, buildings = buildings, addSuccess = addFlag, bookSuccess = bookFlag)
   else:
      return redirect(url_for("index"))

@app.route('/handleAddUser', methods = ['GET', 'POST'])
def handleAddUser():
   if isLoggedIn():
      if request.method == 'POST':

         addFlag = False
         admin = request.form['admin-id']
         print(admin)
         current_user = session['username']
         print(current_user)

         current_user_object = getUser(current_user)
         
         if (admin is None or admin.strip() == ""):
            errorMsg = "Please enter an admin netid. User not added."

         else:
            admin = admin.strip()
            recipient = admin + "@princeton.edu"
            msg = Message('QRoom Admin',
                  sender='qroomteam@gmail.com',
                  recipients=[recipient])
            msg.body = 'You have been added as an admin.'

            try: 
               mail.send(msg)
               print("I sent the mail")
               errorMsg = addAdmin(current_user_object, admin)
               
               if errorMsg == "":
                  addFlag = True

            except Exception as e:
               print("failed to send mail to user")
               print("Exception received, ", str(e))
               errorMsg = "Could not contact the user."

            #isAdmin = ('admin' in session is True)
            print("in handle user, ", errorMsg)
            return redirect(url_for("admin", addMessage = errorMsg, bookMessage = '', addFlag = addFlag, bookFlag = False))
         
      else:
         print("Error in handle add user: not a post request")
   else:
      return redirect(url_for("index"))

@app.route('/handleSchedule', methods = ['GET', 'POST'])
def handleSchedule():
    if isLoggedIn():
        if request.method == 'POST':
            bookFlag = False
            print("printing request form", request.form.items())
            for key, val in request.form.items():
               print(key, val)
            building_id = request.form['building']
            room_id = request.form['room-id']
            start_time = request.form['start-time']
            end_time = request.form['end-time']

            # check that the room id is in the building
            # building_object = getBuildingObject(building_id)
            room_object = getRoomObject(room_id, building_id)
            if room_object is None:
                roomMessage = 'Please enter a valid room.'
                return redirect(url_for("admin", addMessage = '', bookMessage = roomMessage, addFlag = False, bookFlag = bookFlag))

            # make a datetime object for the start and end
            start_year = start_time[:4]
            start_month = start_time[5:7]
            start_day = start_time[8:10]
            start_hour = start_time[11:13]
            start_minutes = start_time[14:16]
            start_meridiem = start_time[20:22]

            end_year = end_time[:4]
            end_month= end_time[5:7]
            end_day = end_time[8:10]
            end_hour = end_time[11:13]
            end_minutes = end_time[14:16]
            end_meridiem = end_time[20:22]

            starting_hour = int(start_hour)
            ending_hour = int(end_hour)

            if (start_meridiem == "AM" and starting_hour == 12):
               starting_hour = 0
            if (start_meridiem == "PM" and starting_hour >= 1 and starting_hour < 12):
               starting_hour += 12
            if (end_meridiem == "AM" and ending_hour == 12):
               ending_hour = 0
            if (end_meridiem == "PM" and ending_hour >= 1 and ending_hour < 12):
               ending_hour += 12

            start = datetime(int(start_year), int(start_month), int(start_day), starting_hour, int(start_minutes))
            end = datetime(int(end_year), int(end_month), int(end_day), ending_hour, int(end_minutes))
            current_user = session['username']
            current_user_object = getUser(current_user)

            eventMessage = bookRoomSchedule(current_user_object, room_object, start, end)
            if eventMessage != '':
                return redirect(url_for("admin", addMessage = '', bookMessage = eventMessage, addFlag = False, bookFlag = bookFlag))

            bookFlag = True
            return redirect(url_for("admin", addMessage = '', bookMessage = eventMessage, addFlag = False, bookFlag = bookFlag))

@app.route('/currentBooking', methods = ['GET', 'POST'])
def currentBooking():
    if isLoggedIn():
        building = request.args.get('building')
        room = request.args.get('room')
        time = str(request.args.get('fullTime'))
        year = int(time[0:4])
        month = int(time[5:7])
        day = int(time[8:10])
        hour = int(time[11:13])
        minute = int(time[14:16])
        end_time = datetime(year, month, day, hour, minute, 0, 0)


        if 'admin' in session:
            return render_template("currentBooking.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], fullTime = time, admin = True)
        else:
            return render_template("currentBooking.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], fullTime = time, admin = False)

    else:
       return redirect(url_for("index"))


def isLoggedIn():
   # print(session['username'])
   if 'username' in session:
      return True
   return False

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug = True)
