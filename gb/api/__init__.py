from flask import Blueprint

home = Blueprint(name = "home",
                 import_name = __name__,
                 template_folder = 'templates',
                 static_folder = 'static')

from . import views
