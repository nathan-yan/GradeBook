from flask import Blueprint

api = Blueprint(name = "api",
                 import_name = __name__,
                 template_folder = 'templates',
                 static_folder = 'static')

from . import views
