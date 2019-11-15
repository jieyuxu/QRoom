from flask import Flask, request, render_template, url_for, redirect
from flask import session
from flask_cas import CAS
from flask_cas import login_required
import os
from utils.api import *

app = Flask(__name__)
app.secret_key = os.urandom(24)

########## CAS AUTHENTICATION ###########
cas = CAS(app)
app.config['CAS_SERVER'] = "https://fed.princeton.edu/cas/login"
app.config['CAS_AFTER_LOGIN'] = 'caslogin'
app.config['CAS_AFTER_LOGOUT'] = 'http://localhost:5000/caslogout'
app.config['CAS_LOGIN_ROUTE'] = '/cas'
#########################################

@app.route('/')
def index():
   if isLoggedIn():
      return redirect(url_for('profile'))

   return render_template("index.html",loggedin = isLoggedIn())

@app.route('/caslogin')
def caslogin():
   print(app.config['CAS_USERNAME_SESSION_KEY'])
   if cas.username is not None:
      print("user: ", cas.username)
      session['username'] = cas.username

      # add user to database if not in there
      # returns user object that was added
      user = getUser(str(cas.username))

   return redirect(url_for('profile'))

@app.route('/caslogout')
def caslogout():
   if isLoggedIn():
      session.pop('username')
   return redirect(url_for('index'))

@app.route('/profile')
def profile():
   if isLoggedIn():
      return render_template("profile.html", loggedin = isLoggedIn(), username = cas.username)

   else:
      return redirect(url_for("index"))

@app.route('/buildings')
def buildings():
    if isLoggedIn():
        buildings_query = getBuildings()
        buildings = []
        for b in buildings_query:
            buildings.append(b.building_name)
        return render_template("buildings.html", loggedin = isLoggedIn(),
                                username = cas.username, buildings=buildings)
    else:
      return redirect(url_for("index"))

@app.route('/rooms')
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
        return render_template("rooms.html", loggedin = isLoggedIn(),
                                username = cas.username, building=building, rooms=rooms)
    else:
       return redirect(url_for("index"))

@app.route('/bookRoom')
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
      for i in range(number):
          time = getDelta(datetime.now(), THIRTY_MIN + THIRTY_MIN * i)
          times.append(str(time)[11:16])

      return render_template("bookRoom.html", loggedin = loggedin, username = cas.username, building=building, room=room, times = times)
   else:
      return redirect(url_for("index"))
   
@app.route('/viewRoom')
def viewRoom(): 
   if isLoggedIn():
      building = request.args.get('building')
      room = request.args.get('room')
      # TODO: get if room is available from the database #
      isAvailable = false
      # TODO: get schedule from the database #
      times = ['1:00 PM', '1:30 PM', '3:00 PM', '3:30 PM']
      return render_template("viewRoom.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, times = times, isAvailable = isAvailable)
   else:
      return redirect(url_for("index"))
   
   THIRTY_MIN = 30

   if isLoggedIn():
      building = request.args.get('building')
      room = str(request.args.get('room'))
      room_object = getRoomObject(room, building)

      number = displayBookingButtons(room_object) # number of buttons to display
      times = []
      for i in range(number):
         time = getDelta(datetime.now(), THIRTY_MIN + THIRTY_MIN * i)
         times.append(str(time)[11:16])

      return render_template("bookRoom.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, times = times)
   else:
      return redirect(url_for("index"))

@app.route('/confirmation')
def confirmation():
    if isLoggedIn():
        building = request.args.get('building')
        room = request.args.get('room')
        # assuming time is a string form of datetime object, like '2021-08-28 05:55:59.342380'
        time = str(request.args.get('time'))
      
        # assuming 'username' means netid
        user = getUserObject('username')
        room_object = getRoomObject(room, building)
        year = int(time[0:4])
        month = int(time[5:7])
        day = int(time[8:10])
        hour = int(time[11:13])
        minute = int(time[14:16])
        end_time = datetime(year, month, day, hour, minute, 0, 0)

        # updates database, returns empty string if successful
        error = bookRoomAdHoc(user, room_object, end_time)

        return render_template("confirmation.html", loggedin = isLoggedIn(), username = cas.username, building=building, room=room, time = time)
    else:
      return redirect(url_for("index"))

def isLoggedIn():
   # print(session['username'])
   if 'username' in session:
      return True
   return False

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug = True)