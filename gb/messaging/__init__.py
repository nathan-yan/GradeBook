from flask import Blueprint
from flask_socketio import SocketIO

messaging = Blueprint(name = "messaging",
                 import_name = __name__,
                 template_folder = 'templates',
                 static_folder = 'static')

from . import views
