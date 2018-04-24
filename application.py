from flask import Flask
from gb.home import home
from gb.api import api

application = Flask(__name__)

# Register blueprints
application.register_blueprint(home)
application.register_blueprint(api)

if __name__ == "__main__":
    application.run(host = '0.0.0.0', debug = True)

