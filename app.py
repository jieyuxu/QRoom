from flask import Flask, render_template
from flask_cas import CAS
from flask_cas import login_required
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
########## CAS AUTHENTICATION ###########
cas = CAS(app)
app.config['CAS_SERVER'] = "https://fed.princeton.edu/cas/login"
app.config['CAS_AFTER_LOGIN'] = 'profile'
app.config['CAS_AFTER_LOGOUT'] = 'http://localhost:5000'
app.config['CAS_LOGIN_ROUTE'] = '/cas'
#########################################

@app.route('/')
def index():
   return render_template("index.html")

@app.route('/profile')
def profile():
   return render_template("index.html")

if __name__ == '__main__':
   app.run(debug=True)