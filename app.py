from flask import Flask, render_template, session, url_for, redirect
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
   

if __name__ == '__main__':
   app.run(debug=True)