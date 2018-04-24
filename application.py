from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, send

from gb.home import home
from gb.messaging import messaging

import gb.db 
import gb.auth
import gb.exceptions

import requests
import time
import json

from bson import BSON 
from bson import json_util

application_ = Flask(__name__)

application_.register_blueprint(home)
application_.register_blueprint(messaging, url_prefix = '/messaging')

application = SocketIO(application_)
from gb.messaging import views

views.init_application(application)

if __name__ == "__main__":
    application.run(application_, host = '0.0.0.0', debug = True)

