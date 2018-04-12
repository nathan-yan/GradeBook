from flask import Flask
from gb.home import home

app = Flask(__name__)
app.register_blueprint(home)

app.run(host = '192.168.1.22', debug = True)

