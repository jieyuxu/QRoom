from flask import Flask, request, render_template, url_for, redirect, current_app, json, make_response
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
import re

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
# app.config['CAS_AFTER_LOGOUT'] = 'http://localhost:5000/caslogout'
app.config['CAS_LOGIN_ROUTE'] = '/cas'
#########################################

@app.route('/')
def index():
   if isLoggedIn():
      return redirect(url_for('booking'))
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
   return redirect(url_for('booking'))

@app.route('/caslogout')
def caslogout():
   if isLoggedIn():
      session.pop('username')
      if 'admin' in session:
          session.pop('admin')
      session.modified = True
   return redirect(url_for('index'))

@app.route('/booking')
def booking():
   if isLoggedIn():
      event_query = getUserEvent(session['username'])
      buildingname=''
      roomname=''
      eventid=''

      if len(event_query) == 0:
          if 'admin' in session:
             return render_template("booking.html", loggedin = isLoggedIn(), username = cas.username, errorMsg = "No Bookings", admin = True)
          else:
             return render_template("booking.html", loggedin = isLoggedIn(), username = cas.username, errorMsg = "No Bookings", admin = False)

      buildings_query = getBuildings()
      rooms = []
      for b in buildings_query:
         rooms_query = list(getRooms(b).keys())
         for r in rooms_query:
            s = b.building_name + " - " + r.room_name
            rooms.append(s)

      calender = {}
      for event in event_query:
         # check end time and if it has passed
         if (current_dt() > event.end_time):
            continue

         # check if start month, year in dictionary
         start_time = event.start_time
         end_time = event.end_time
         mon_yr = str(start_time.strftime("%B")) + ' ' + str(start_time.year)

         if mon_yr in calender:
            events = calender[mon_yr]
         else:
            events = []

         # get event details, store into dictionary
         eventDetails = {}
         eventDetails['StartTime'] = get_month_day(start_time) +  ', ' + twelve_hour_time(start_time)
         eventDetails['EndTime'] = get_month_day(end_time) +  ', ' + twelve_hour_time(end_time)
         eventDetails['FullEndTime'] = end_time
         location = getBuildingRoomName(event.room_id)
         eventDetails['buildingName'] = location[0]
         eventDetails['roomName'] = location[1]
         eventDetails['roomHeader'] = location[0] + " " + location[1]
         eventDetails['eventId'] = event.event_id
         eventDetails['title'] = event.event_title

         eventDetails['start_year'] = start_time.year
         eventDetails['start_month'] = start_time.month
         eventDetails['start_day'] = start_time.day
         eventDetails['start_hour'] = start_time.hour
         eventDetails['start_minutes'] = start_time.minute
         eventDetails['start_seconds'] = start_time.second

         eventDetails['end_year'] = end_time.year
         eventDetails['end_month']= end_time.month
         eventDetails['end_day'] = end_time.day
         eventDetails['end_hour'] = end_time.hour
         eventDetails['end_minutes'] = end_time.minute
         eventDetails['end_seconds'] = end_time.second

         # add dictionary into events assos. with month, year and add [back] to calender
         events.append(eventDetails)
         calender[mon_yr] = events

         # calendar is a dictionary with key = a month/year string and value = events list
         # events is a list of eventdetails dictionaries
         # eventdetails is a dictionary containing all of the information for a specific event within the month/yr

      if 'admin' in session:
         return render_template("booking.html", loggedin = isLoggedIn(), username = cas.username, events = calender, admin = True, rooms=rooms)
      else:
         return render_template("booking.html", loggedin = isLoggedIn(), username = cas.username, events = calender, admin = False, rooms=rooms)
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
         times.append(twelve_hour_time(time))
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

@app.route('/editReservation', methods=['GET', 'POST'])
def editReservation():
   if isLoggedIn():
      if request.method == 'POST':
         adminStatus = 'admin' in session
         # room_id is a room number and building_id is the building name
         # building_id = request.form['building']
         room_id = request.form['room-id']
         start_time = request.form['start-time']
         end_time = request.form['end-time']
         title = request.form['title']
         event_id = request.form['eventid']
         fullTime = start_time + ' - ' + end_time

         if title == '':
            title = '< No Event Title >'

         if not adminStatus:
            errorMsg = "You do not have administrative access."
            return render_template("editConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, error=errorMsg, fullTime=fullTime, room=room_id)


         event_object = getEventObject(event_id)
         if event_object is None:
            print("This should not occur! Invalid event")
            return redirect(url_for('booking'))

         regex = "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [A,P]M"
         startMatch = re.search(regex, start_time)
         endMatch = re.search(regex, end_time)
         print(start_time)
         if startMatch is None:
            errorMsg = 'Please enter a valid start time. Select a time by clicking on the calendar icon, or enter a time in the format year-month-day hour:minutes:seconds AM/PM'
            return render_template("editConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, error=errorMsg, fullTime=fullTime, room=room_id)
         if endMatch is None:
            errorMsg = 'Please enter a valid end time. Select a time by clicking on the calendar icon, or enter a time in the format year:month:day:hour:minutes:seconds:milliseconds:AM/PM'
            return render_template("editConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, error=errorMsg, fullTime=fullTime, room=room_id)

         # make a datetime object for the start and end
         start_year = start_time[:4]
         start_month = start_time[5:7]
         start_day = start_time[8:10]
         start_hour = start_time[11:13]
         start_minutes = start_time[14:16]
         start_seconds = start_time[17:19]
         start_meridiem = start_time[20:22]

         end_year = end_time[:4]
         end_month= end_time[5:7]
         end_day = end_time[8:10]
         end_hour = end_time[11:13]
         end_minutes = end_time[14:16]
         end_seconds = end_time[17:19]
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

         start = datetime(int(start_year), int(start_month), int(start_day), starting_hour, int(start_minutes), int(start_seconds))
         end = datetime(int(end_year), int(end_month), int(end_day), ending_hour, int(end_minutes), int(end_seconds))
         fullTime = "Start: " + get_month_day(start) + ' ' + twelve_hour_time(start) + "\nEnd: " + get_month_day(end) + ' ' + twelve_hour_time(end)
         current_user = session['username']
         current_user_object = getUser(current_user)

         location = room_id.split(' - ', 1)
         room_object = getRoomObject(location[1], location[0])
         errorMsg = editRoomSchedule(current_user_object, room_object, start, end, event_object, title)
         return render_template("editConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, error=errorMsg, fullTime=fullTime, room=room_id)

   else:
        return redirect(url_for("index"))

@app.route('/viewRoom', methods=['GET', 'POST'])
def viewRoom():
    if isLoggedIn():
        START_TIME = 0
        END_TIME = 1
        BOOKER = 2

        building = request.args.get('building')
        room = request.args.get('room')
        room_object = getRoomObject(room,building)
        group = getGroup(room_object)

        markPassed()

        # get current time and get delta 30
        counter_time = get30(current_dt())
        month_day = get_month_day(current_dt())

        # get all events in room for a certain day
        events = getEvents(getRoomObject(room, building))
        times_blocked = []

        for e in events:
            times_blocked.append([e.start_time, e.end_time, e.net_id])

        # dictionary of times with array object
        # object: [boolean for availability, name of owner of event (else '')]
        dictionary = {}

        while (counter_time.time() != time(0, 0)):
            check = counter_time - timedelta(seconds=1)

            if not isGroupOpen(group,check):
                dictionary[twelve_hour_time(counter_time)] = [False, '']
                counter_time = add30(counter_time)
                continue

            for t in times_blocked:
                if inRange(t[START_TIME], t[END_TIME], check):
                    dictionary[twelve_hour_time(counter_time)] = [False, t[BOOKER]]
                    break

            # if still not added into dictionary
            if counter_time not in dictionary.keys():
                dictionary[twelve_hour_time(counter_time)] = [True, '']

            counter_time = add30(counter_time)

        if 'admin' in session:
            return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username,
                                    building=building, room=room, times = dictionary, month_day = month_day, admin = True)
        else:
            return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username,
                                    building=building, room=room, times = dictionary, month_day = month_day, admin = False)
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
        fullTime = get_month_day(end_time) +  ' ' + twelve_hour_time(end_time)

        if 'admin' in session:
           return render_template("confirmation.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = fullTime, admin = True)
        else:
           return render_template("confirmation.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = fullTime, admin = False)
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
      rooms = []
      for b in buildings_query:
         rooms_query = list(getRooms(b).keys())
         for r in rooms_query:
            s = b.building_name + " - " + r.room_name
            rooms.append(s)

      return render_template("admin.html", loggedin = isLoggedIn(), username = cas.username, admin = 'admin' in session, rooms = rooms)
   else:
      return redirect(url_for("index"))

@app.route('/handleAddUser', methods = ['GET', 'POST'])
def handleAddUser():
   if isLoggedIn():
      if request.method == 'POST':

         admin = request.form['admin-id']

         current_user = session['username']
         current_user_object = getUser(current_user)
         adminStatus = 'admin' in session

         if not adminStatus:
            errorMsg = "You do not have administrative access."
            return render_template("newAdminConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, addMessage=errorMsg, newUser=admin)

         if (admin is None or admin.strip() == ""):
            errorMsg = "Please enter an admin netid."
            return render_template("newAdminConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, addMessage=errorMsg, newUser=admin)

         else:
            admin = admin.strip()
            recipient = admin + "@princeton.edu"
            msg = Message('QRoom Admin',
                  sender='qroomteam@gmail.com',
                  recipients=[recipient])
            msg.body = 'Weclome to the QRoom team! You have been added as an admin by ' + current_user + '. Administrative access allows you to access the Admin Portal, where you can add new users as admins, book rooms ahead of time, and monitor all current bookings. If you think this email was sent to you by mistake, please reply to us at qroomteam@gmail.com.'

            try:
               mail.send(msg)
               errorMsg = addAdmin(current_user_object, admin)

            except Exception as e:
               print("failed to send mail to user")
               print("Exception received, ", str(e))
               errorMsg = "Could not contact the user. User not added as admin"

            print("error message in handle user, ", errorMsg)
            return render_template("newAdminConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, addMessage=errorMsg, newUser=admin)
      else:
         print("Error in handle add user: not a post request")
   else:
      return redirect(url_for("index"))

@app.route('/handleSchedule', methods = ['GET', 'POST'])
def handleSchedule():
   if isLoggedIn():
      if request.method == 'POST':
         adminStatus = 'admin' in session
         print("printing request form", request.form.items())
         for key, val in request.form.items():
            print(key, val)
         room_id = request.form['room-id']
         start_time = request.form['start-time']
         end_time = request.form['end-time']
         title = request.form['title']
         fullTime = start_time + ' - ' + end_time

         if title == '':
            title = '< No Event Title >'

         if not adminStatus:
            errorMsg = "You do not have administrative access."
            return render_template("scheduledConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, error=errorMsg, fullTime=fullTime, room=room_id)

         regex = "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} [A,P]M"
         startMatch = re.search(regex, start_time)
         endMatch = re.search(regex, end_time)
         print(start_time)
         if startMatch is None:
            errorMsg = 'Please enter a valid start time. Select a time by clicking on the calendar icon, or enter a time in the format year-month-day hour:minutes:seconds AM/PM'
            return render_template("scheduledConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, error=errorMsg, fullTime=fullTime, room=room_id)
         if endMatch is None:
            errorMsg = 'Please enter a valid end time. Select a time by clicking on the calendar icon, or enter a time in the format year:month:day:hour:minutes:seconds:milliseconds:AM/PM'
            return render_template("scheduledConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, error=errorMsg, fullTime=fullTime, room=room_id)

         # make a datetime object for the start and end
         start_year = start_time[:4]
         start_month = start_time[5:7]
         start_day = start_time[8:10]
         start_hour = start_time[11:13]
         start_minutes = start_time[14:16]
         start_seconds = start_time[17:19]
         start_meridiem = start_time[20:22]

         end_year = end_time[:4]
         end_month= end_time[5:7]
         end_day = end_time[8:10]
         end_hour = end_time[11:13]
         end_minutes = end_time[14:16]
         end_seconds = end_time[17:19]
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

         start = datetime(int(start_year), int(start_month), int(start_day), starting_hour, int(start_minutes), int(start_seconds))
         end = datetime(int(end_year), int(end_month), int(end_day), ending_hour, int(end_minutes), int(end_seconds))
         current_user = session['username']
         current_user_object = getUser(current_user)

         location = room_id.split(' - ', 1)
         room_object = getRoomObject(location[1], location[0])
         errorMsg = bookRoomSchedule(current_user_object, room_object, start, end, title)
         fullTime = "Start: " + get_month_day(start) + ' ' + twelve_hour_time(start) + "\nEnd: " + get_month_day(end) + ' ' + twelve_hour_time(end)


         return render_template("scheduledConfirmation.html", loggedin=isLoggedIn(), username=cas.username, admin=adminStatus, error=errorMsg, fullTime=fullTime, room=room_id)

@app.route('/roomSchedule')
def roomSchedule():
   building=request.args.get('building')
   room=request.args.get('room')

   room_object = getRoomObject(room, building)
   event_query = getEventsSorted(room_object)

   calender = {}
   for event in event_query:
      # check end time and if it has passed
      if (current_dt() > event.end_time):
         continue

      # check if start month, year in dictionary
      start_time = event.start_time
      end_time = event.end_time
      mon_yr = str(start_time.strftime("%B")) + ' ' + str(start_time.year)

      if mon_yr in calender:
         events = calender[mon_yr]
      else:
         events = []

      # get event details, store into dictionary
      eventDetails = {}
      eventDetails['StartTime'] = get_month_day(start_time) + ', ' + twelve_hour_time(start_time)
      eventDetails['EndTime'] = get_month_day(end_time) + ', ' + twelve_hour_time(end_time)
      #eventDetails['eventId'] = event.event_id
      eventDetails['title'] = event.event_title
      eventDetails['owner'] = event.net_id

      # add dictionary into events assos. with month, year and add [back] to calender
      events.append(eventDetails)
      calender[mon_yr] = events

      # calendar is a dictionary with key = a month/year string and value = events list
      # events is a list of eventdetails dictionaries
      # eventdetails is a dictionary containing all of the information for a specific event within the month/yr
   response = make_response(render_template("roomResults.html", loggedin = isLoggedIn(), username = cas.username, events = calender, admin = True))
   return response

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
        print(eventid)
        year = int(time[0:4])
        month = int(time[5:7])
        day = int(time[8:10])
        hour = int(time[11:13])
        minute = int(time[14:16])
        second = int(time[17:19])
        end_time = datetime(year, month, day, hour, minute, second, 0)
        seconds = (end_time - current_dt()).total_seconds()

        if 'admin' in session:
            return render_template("currentBooking.html", seconds = seconds, loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = twelve_hour_time(end_time), eventid = eventid, admin = True)
        else:
            return render_template("currentBooking.html", seconds = seconds, loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = twelve_hour_time(end_time), eventid = eventid, admin = False)

    else:
       return redirect(url_for("index"))


def isLoggedIn():
   # print(session['username'])
   if 'username' in session:
      return True
   return False

@app.route('/checkTime', methods=['GET', 'POST'])
def checkTime():
    if isLoggedIn() and request.method == 'POST':
        if request.is_json:
            content = request.get_json()
            eventid = content['eventid']
            endtime = getEventObject(eventid).end_time
            deadline = endtime - timedelta(minutes=10)
            timenow = current_dt()
            print("endtime is " + str(endtime))
            print("now is " + str(timenow))
            print("deadline is " + str(deadline))

        if endtime < timenow:
            releaseEvent(getEventObject(eventid))
            return "Expired"
        elif deadline <= timenow:
            return "True"
        else:
            return "False"
    else:
        return redirect(url_for("index"))


@app.route('/extend', methods=['GET'])
def extend():
    print("in extend stay")
    print("am i logged in?", isLoggedIn())
    print("request method", request.method)
    print(request.args)
    print(request.args.get('eventid'))
    if isLoggedIn():
        THIRTY_MIN = 30
        loggedin = True
        eventid = request.args.get("eventid")
        print(eventid)
        event = getEventObject(eventid)
        event.passed = True

        roomid = event.room_id
        result = getBuildingRoomName(roomid)

        room = getRoomObject(result[1], result[0])
        building=result[0]

        number = displayExtendBookingButtons(room) # number of buttons to display
        print(number)
        latitude, longitude = getLatLong(building)
        times = []
        fullTimes = [] # military time
        time = get30(current_dt())
        for i in range(number):
            time = add30(time)
            times.append(str(time)[11:16])
            fullTimes.append(str(time))
        print(times)
        print(fullTimes)
        event.passed = False

        if 'admin' in session:
            return render_template("extend.html", loggedin = loggedin, username = cas.username, building=building,\
            room=result[1], eventid = eventid, times = times, fullTimes = fullTimes, admin = True, latitude=latitude, longitude=longitude)
        else:
            return render_template("extend.html", loggedin = loggedin, username = cas.username, building=building, \
            room=result[1], eventid = eventid, times = times, fullTimes = fullTimes, admin = False, latitude=latitude, longitude=longitude)
    else:
        return redirect(url_for("index"))

@app.route('/confirmExtend', methods=['GET', 'POST'])
def confirmExtend():
    eventid = request.args.get("eventid")
    print(eventid)
    event = getEventObject(eventid)
    print(event)
    roomid = event.room_id
    result = getBuildingRoomName(roomid)
    building=result[0]
    time = str(request.args.get('fullTime'))
    year = int(time[0:4])
    month = int(time[5:7])
    day = int(time[8:10])
    hour = int(time[11:13])
    minute = int(time[14:16])
    end_time = datetime(year, month, day, hour, minute, 0, 0)

    updateEvent(event, end_time)
    print("updated event")

    if 'admin' in session:
       return render_template("confirmExtend.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=result[1], time = str(time)[11:16], fullTime = time, admin = True)
    else:
        return render_template("confirmExtend.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=result[1], time = str(time)[11:16], fullTime = time, admin = False)



if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug = True)
