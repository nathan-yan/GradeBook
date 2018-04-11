from flask import Flask
from gb.home import home

app = Flask(__name__)
app.register_blueprint(home)

app.run(debug = True)

