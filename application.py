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

application = Flask(__name__)

# No strict slashes to deal with issues with trailing slashes
application.url_map.strict_slashes = False

application.register_blueprint(home)
application.register_blueprint(messaging, url_prefix = '/messaging')

application_ = SocketIO(application)
from gb.messaging import views

views.init_application(application_)

if __name__ == "__main__":
    application_.run(application, debug = True)

