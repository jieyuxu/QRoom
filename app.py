from flask import Flask, request, render_template, url_for, redirect
from flask import session
import os
from utils.api import *
from flask_sqlalchemy_session import flask_scoped_session
from utils.base import session_factory
from distance import distance
from CAS import CAS
from CAS import login_required
from pywebpush import webpush, WebPushException
from pytz import timezone

app = Flask(__name__)
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
        event_query = getUserEvent(session['username'])
        buildingname=''
        roomname=''
        eventid=''

        # an array of eventDetails
        events = []
        for event in event_query:
            # check end time and if it has passed
            if (current_dt() > event.end_time):
              continue

            eventDetails = {}
            eventDetails['StartTime'] = event.start_time
            eventDetails['EndTime'] = event.end_time
            room = getBuildingRoomName(event.room_id)
            eventDetails['buildingName'] = room[0]
            eventDetails['roomName'] = room[1]
            eventDetails['eventId'] = event.event_id
            events.append(eventDetails)

        if 'admin' in session:
            return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username,
                           events = events, admin = True)
        else:
            return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username,
                           events = events, admin = False)
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

      latitude, longitude = getLatLong(building)
      times = []
      fullTimes = [] # military time
      for i in range(number):
         if i == 0:
            time = get30(current_dt())
         else:
            time = add30(time)
         times.append(str(time)[11:16])
         fullTimes.append(str(time))
      print(times)
      print(fullTimes)
      if 'admin' in session:
         return render_template("bookRoom.html", loggedin = loggedin, username = cas.username, building=building,\
          room=room, times = times, fullTimes = fullTimes, admin = True, latitude=latitude, longitude=longitude)
      else:
         return render_template("bookRoom.html", loggedin = loggedin, username = cas.username, building=building, \
         room=room, times = times, fullTimes = fullTimes, admin = False, latitude=latitude, longitude=longitude)

   else:
      return redirect(url_for("index"))

@app.route('/viewRoom', methods=['GET', 'POST'])
def viewRoom():
    if isLoggedIn():
        building = request.args.get('building')
        room = request.args.get('room')
        markPassed()
        print(room)
        print(building)
        room_object = getRoomObject(room,building)
        if room_object is None:
            print('hi')
        group = getGroup(room_object)

        # get current time and get delta 30
        time = get30(current_dt())
        print(time)

        # get all events in room for a certain day
        events = getEvents(getRoomObject(room, building))
        times_blocked = []

        for e in events:
            times_blocked.append([e.start_time, e.end_time])
            print([e.start_time, e.end_time])

            dictionary = {}
        while time.hour != 0:
            for t in times_blocked:
                check = time - timedelta(seconds=1)

                if inRange(t[0], t[1], check) or not isGroupOpen(group,check):
                    dictionary[time] = False
                    break

            if time not in dictionary.keys():
                dictionary[time] = True

            time = add30(time)

        isAvailable = False

        if 'admin' in session:
            return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, times = dictionary, isAvailable = isAvailable, admin = True)
        else:
            return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, times = dictionary, isAvailable = isAvailable, admin = False)
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
      if event is not None:
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
            addMessage = request.args.get('bookMessage')

        bookFlag = False
        addFlag = False
        if 'bookFlag' in request.args:
            bookFlag = request.args.get('bookFlag')
        if 'addFlag' in request.args:
            addFlag = request.args.get('addFlag')

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
            current_user = getUser(cas.username)
            errorMsg = addAdmin(current_user, admin)
            added_user = getUser(admin)
            print("is user an admin?", added_user.admin)
            if errorMsg == '':
                addFlag = True
            isAdmin = ('admin' in session is True)
            return redirect(url_for("admin", addMessage = errorMsg, bookMessage = '', addFlag = addFlag, bookFlag = False))
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
            start_year = request.form['starting-year-id']
            start_month = request.form['starting-month-id']
            start_day = request.form['starting-day-id']
            start_hour = request.form['starting-hour-id']
            start_minutes = request.form['starting-min-id']
            end_year = request.form['ending-year-id']
            end_month = request.form['ending-month-id']
            end_day = request.form['ending-day-id']
            end_hour = request.form['ending-hour-id']
            end_minutes = request.form['ending-min-id']

            # check that the room id is in the building
            # building_object = getBuildingObject(building_id)
            room_object = getRoomObject(room_id, building_id)
            if room_object is None:
                roomMessage = 'Please enter a valid room.'
                return redirect(url_for("admin", addMessage = '', bookMessage = roomMessage, addFlag = False, bookFlag = bookFlag))

            # make a datetime object for the start and end
            start = datetime(int(start_year), int(start_month), int(start_day), int(start_hour), int(start_minutes))
            end = datetime(int(end_year), int(end_month), int(end_day), int(end_hour), int(end_minutes))
            current_user = getUserObject(cas.username)

            eventMessage = bookRoomSchedule(current_user, room_object, start, end)
            if eventMessage != '':
                return redirect(url_for("admin", addMessage = '', bookMessage = eventMessage, addFlag = False, bookFlag = bookFlag))

            bookFlag = True
            return redirect(url_for("admin", addMessage = '', bookMessage = eventMessage, addFlag = False, bookFlag = bookFlag))

@app.route('/currentBooking', methods = ['GET', 'POST'])
def currentBooking():
    if isLoggedIn():
        building = request.args.get('building')
        print(building)
        room = request.args.get('room')
        print(room)
        time = str(request.args.get('fullTime'))
        print(time)
        year = int(time[0:4])
        month = int(time[5:7])
        day = int(time[8:10])
        hour = int(time[11:13])
        minute = int(time[14:16])
        end_time = datetime(year, month, day, hour, minute, 0, 0)
        seconds = (end_time - current_dt()).total_seconds()

        if 'admin' in session:
            return render_template("currentBooking.html", seconds = seconds, loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], admin = True)
        else:
            return render_template("currentBooking.html", seconds = seconds, loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], admin = False)

    else:
       return redirect(url_for("index"))


def isLoggedIn():
   # print(session['username'])
   if 'username' in session:
      return True
   return False

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug = True)
