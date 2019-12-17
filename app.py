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
app.config['CAS_AFTER_LOGOUT'] = 'http://princeton-qroom.herokuapp.com/caslogout'
# app.config['CAS_AFTER_LOGOUT'] = 'localhost:5000/caslogout'
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

        calender = {}
        for event in event_query:
            # check end time and if it has passed
            if (current_dt() > event.end_time):
              continue

            # check if start month, year in dictionary
            start_time = event.start_time
            mon_yr = str(start_time.strftime("%B")) + ' ' + str(start_time.year)

            if mon_yr in calender:
                events = calender[mon_yr]
            else:
                events = []

            # get event details, store into dictionary
            eventDetails = {}
            eventDetails['StartTime'] = start_time
            eventDetails['EndTime'] = event.end_time
            room = getBuildingRoomName(event.room_id)
            eventDetails['buildingName'] = room[0]
            eventDetails['roomName'] = room[1]
            eventDetails['eventId'] = event.event_id
            eventDetails['title'] = event.event_title

            # add dictionary into events assos. with month, year and add [back] to calender
            events.append(eventDetails)
            calender[mon_yr] = events

        if 'admin' in session:
            return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username,
                           events = calender, admin = True)
        else:
            return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username,
                           events = calender, admin = False)
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

        room_object = getRoomObject(room,building)
        group = getGroup(room_object)
        print(group.group_id)

        # get current time and get delta 30
        counter_time = get30(current_dt())

        # get all events in room for a certain day
        events = getEvents(getRoomObject(room, building))
        print(room)
        print(building)
        times_blocked = []

        for e in events:
            times_blocked.append([e.start_time, e.end_time])
            print([e.start_time, e.end_time])

        dictionary = {}

        while (counter_time.time() != time(0, 0)):
            check = counter_time - timedelta(seconds=1)

            if not isGroupOpen(group,check):
                dictionary[counter_time] = False
                counter_time = add30(counter_time)
                continue

            for t in times_blocked:
                if inRange(t[0], t[1], check):
                    dictionary[counter_time] = False
                    break

            # if still not added into dictionary
            if counter_time not in dictionary.keys():
                dictionary[counter_time] = True

            counter_time = add30(counter_time)

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
        user = getUser(session['username'])
        print("THIS IS THE USER", user)
        room_object = getRoomObject(room, building)
        year = int(time[0:4])
        month = int(time[5:7])
        day = int(time[8:10])
        hour = int(time[11:13])
        minute = int(time[14:16])
        end_time = datetime(year, month, day, hour, minute, 0, 0)

        # updates database, returns empty string if successful
        print("username:" + session['username'])
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
            title = request.form['title']

            if title == '':
                title = '< No Event Title >'

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

            eventMessage = bookRoomSchedule(current_user_object, room_object, start, end, title)
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
        eventid = request.args.get('eventid')
        year = int(time[0:4])
        month = int(time[5:7])
        day = int(time[8:10])
        hour = int(time[11:13])
        minute = int(time[14:16])
        end_time = datetime(year, month, day, hour, minute, 0, 0)
        seconds = (end_time - current_dt()).total_seconds()

        if 'admin' in session:
            return render_template("currentBooking.html", seconds = seconds, loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], eventid = eventid, admin = True)
        else:
            return render_template("currentBooking.html", seconds = seconds, loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = str(time)[11:16], eventid = eventid, admin = False)

    else:
       return redirect(url_for("index"))


def isLoggedIn():
   # print(session['username'])
   if 'username' in session:
      return True
   return False

@app.route('/checkTime', methods=['GET', 'POST'])
def checkTime():
    # print("in check time")
    if isLoggedIn() and request.method == 'POST':
        if request.is_json:
            content = request.get_json()
            eventid = content['eventid']
            endtime = getEventObject(eventid).end_time

        if endtime < datetime.now():
            releaseEvent(getEventObject(eventid))
            return "Expired"
        elif (datetime.now() - endtime) <= timedelta(0, 0, 0, 0, 10, 0, 0):
            # print("should show modal")
            return "True"
        else:
            return "False"
    else:
        return redirect(url_for("index"))


@app.route('/extendStay', methods=['GET', 'POST'])
def extendStay():
    print("in extend stay")
    print("am i logged in?", isLoggedIn())
    print("request method", request.method)
    if isLoggedIn() and request.method == 'POST':
        if request.is_json:
            THIRTY_MIN = 30
            loggedin = True
            print("getting content")
            content = request.get_json()
            print("getting eventid")
            eventid = content['eventid']
            event = getEventObject(eventid)

            roomid = event.room_id
            result = getBuildingRoomName(roomid)

            print("getting room")
            room = getRoomObject(result[1], result[0])
            building=result[0]

            url = '/bookRoom?building=' + building + '&room=' + result[1]
            print(url)
            return url
            #
            # number = displayBookingButtons(room) # number of buttons to display
            # times = []
            # fullTimes = [] # military time
            # for i in range(number):
            #     if i == 0:
            #         continue
            #     else:
            #         time = add30(time)
            #     times.append(str(time)[11:16])
            #     fullTimes.append(str(time))
            #     print(times)
            #     print(fullTimes)
            # if 'admin' in session:
            #     print('rendering bookroom')
            #     return render_template("bookRoom.html", loggedin = loggedin, username = cas.username, building=building, room=room, times = times, fullTimes = fullTimes, admin = True)
            # else:
            #     return render_template("bookRoom.html", loggedin = loggedin, username = cas.username, building=building, room=room, times = times, fullTimes = fullTimes, admin = False)
    else:
        print("in redirect")
        return redirect(url_for("index"))

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug = True)
