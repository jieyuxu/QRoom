from flask import Flask, request, render_template, url_for, redirect
from flask import session
import os
from utils.api import *
from flask_sqlalchemy_session import flask_scoped_session
from utils.base import session_factory
from CAS import CAS
from CAS import login_required

app = Flask(__name__)
app.secret_key = 'stop bothering me honey'
# print(os.random(24))
sess = flask_scoped_session(session_factory, app)

########## CAS AUTHENTICATION ###########
cas = CAS(app)
app.config['CAS_SERVER'] = "https://fed.princeton.edu/cas/login"
app.config['CAS_AFTER_LOGIN'] = 'caslogin'
app.config['CAS_AFTER_LOGOUT'] = 'http://localhost:8000/caslogout'
app.config['CAS_LOGIN_ROUTE'] = '/cas'
#########################################

@app.route('/')
def index():
   if isLoggedIn():
      return redirect(url_for('profile'))

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
      if event is not None:
         eventDetails['Start Time'] = event.start_time
         eventDetails['End Time'] = event.end_time

      if 'admin' in session:
         return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username, event=eventDetails, admin = True)
      else:
         return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username, event=eventDetails, admin = False)
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
        rooms = []
        for r in rooms_query.keys():
            if rooms_query[r]:
                rooms.append(r.room_name)
        if 'admin' in session:
           return render_template("rooms.html", loggedin = isLoggedIn(), username = cas.username, building=building, rooms=rooms, admin = True)
        else:
           return render_template("rooms.html", loggedin = isLoggedIn(), username = cas.username, building=building, rooms=rooms, admin = False)
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
      # TODO: get if room is available from the database #
      isAvailable = False
      # TODO: get schedule from the database #
      times = ['1:00 PM', '1:30 PM', '3:00 PM', '3:30 PM']
      length = len(times)
      if 'admin' in session:
         return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, times = times, isAvailable = isAvailable, length = length, admin = True)
      else:
         return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, times = times, isAvailable = isAvailable, length = length, admin = False)
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
        print("confirmatino" + str(type(user)))
        error = bookRoomAdHoc(user, room_object, end_time)

        if 'admin' in session:
           return render_template("confirmation.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], fullTime = time, admin = True)
        else:
           return render_template("confirmation.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], fullTime = time, admin = False)
    else:
      return redirect(url_for("index"))

@app.route('/admin', methods = ['GET', 'POST'])
def admin():
    if isLoggedIn:
        buildings_query = getBuildings()
        buildings = []
        for b in buildings_query:
            buildings.append(b.building_name)

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
            current_user = getUserObject(cas.username)
            errorMsg = addAdmin(current_user, admin)
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
            building_id = request.form('building')
            room_id = request.form('room-id')
            start_year = request.form('starting-year-id')
            start_month = request.form('starting-month-id')
            start_day = request.form('starting-day-id')
            start_hour = request.form('starting-hour-id')
            start_minutes = request.form('starting-min-id')
            end_year = request.form('ending-year-id')
            end_month = request.form('ending-month-id')
            end_day = request.form('ending-day-id')
            end_hour = request.form('ending-hour-id')
            end_minutes = request.form('ending-min-id')

            # check that the room id is in the building
            building_object = getBuildingObject(building_id)
            room_object = getRoomObject(room_id, building_object)
            if room_object is None:
                roomMessage = 'Please enter a valid room.'
                return redirect(url_for("admin", bookMessage = roomMessage, bookFlag = bookFlag))

            # make a datetime object for the start and end
            start = datetime(start_year, start_month, start_day, start_hour, start_minutes)
            end = datetime(end_year, end_month, end_day, end_hour, end_minutes)
            current_user = getUserObject(cas.username)

            eventMessage = bookRoomSchedule(current_user, room_object, start, end)
            if eventMessage != '':
                return redirect(url_for("admin", bookMessage = eventMessage, bookFlag = bookFlag))

            bookFlag = True
            return redirect(url_for("admin", bookMessage = eventMessage, bookFlag = bookFlag))


def isLoggedIn():
   # print(session['username'])
   if 'username' in session:
      return True
   return False

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug = True)
