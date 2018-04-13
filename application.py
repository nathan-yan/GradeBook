from flask import Flask
from gb.home import home

application = Flask(__name__)
application.register_blueprint(home)

if __name__ == "__main__":
    application.run(debug = True)

