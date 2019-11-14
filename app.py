from flask import Flask, request, render_template, session, url_for, redirect
from flask_cas import CAS
from flask_cas import login_required
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
########## CAS AUTHENTICATION ###########
cas = CAS(app)
app.config['CAS_SERVER'] = "https://fed.princeton.edu/cas/login"
app.config['CAS_AFTER_LOGIN'] = 'reroute'
app.config['CAS_AFTER_LOGOUT'] = 'http://localhost:5000'
app.config['CAS_LOGIN_ROUTE'] = '/cas'
#########################################

@app.route('/')
def index():
   loggedin = False 
   
   if 'username' in session: 
      loggedin = True 

   return render_template("index.html" ,loggedin = loggedin)

@app.route('/reroute')
def reroute():
   print(app.config['CAS_USERNAME_SESSION_KEY'])
   if cas.username is not None:
      print("user: ", cas.username) 
      session['username'] = cas.username
   
   return redirect(url_for('profile'))

@app.route('/profile')
def profile():
   loggedin = False 
   if 'username' in session:
      loggedin = True 
      return render_template("profile.html", loggedin = loggedin, username = cas.username)

   else:
      return redirect(url_for("index"))

@app.route('/buildings')
def buildings():
   loggedin = False 
   if 'username' in session:
      loggedin = True 
      # TODO: get buiildings from database #
      buildings = ['Firestone', 'Frist Student Center', 'Lewis Library']
      return render_template("buildings.html", loggedin = loggedin, username = cas.username, buildings=buildings)
   else:
      return redirect(url_for("index"))

@app.route('/rooms')
def rooms():
   loggedin = False 
   if 'username' in session:
      loggedin = True 
      building = request.args.get('building')
      # TODO: get rooms from the database #
      rooms = ['Level 1 Room A', 'Level 2 Room B', 'Level 3 Room C']
      return render_template("rooms.html", loggedin = loggedin, username = cas.username, building=building, rooms=rooms)
   else:
      return redirect(url_for("index"))

@app.route('/bookRoom')
def bookRoom():
   loggedin = False 
   if 'username' in session:
      loggedin = True 
      building = request.args.get('building')
      room = request.args.get('room')
      # TODO: get times from the database #
      times = ['1:00 PM', '1:30 PM', '3:00 PM', '3:30 PM']
      return render_template("bookRoom.html", loggedin = loggedin, username = cas.username, building=building, room=room, times = times)
   else:
      return redirect(url_for("index"))
   
@app.route('/viewRoom')
def viewRoom():
   loggedin = False 
   if 'username' in session:
      loggedin = True 
      building = request.args.get('building')
      room = request.args.get('room')
      # TODO: get if room is available from the database #
      isAvailable = false;
      # TODO: get schedule from the database #
      times = ['1:00 PM', '1:30 PM', '3:00 PM', '3:30 PM']
      return render_template("viewRoom.html", loggedin = loggedin, username = cas.username, building=building, room=room, times = times, isAvailable = isAvailable)
   else:
      return redirect(url_for("index"))

@app.route('/confirmation')
def confirmation():
   loggedin = False 
   if 'username' in session:
      loggedin = True 
      building = request.args.get('building')
      room = request.args.get('room')
      time = request.args.get('time')
      return render_template("confirmation.html", loggedin = loggedin, username = cas.username, building=building, room=room, time = time)
   else:
      return redirect(url_for("index"))


if __name__ == '__main__':
   app.run(debug=True)
