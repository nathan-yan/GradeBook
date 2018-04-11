from flask import Flask

app = Flask(__name__)

from gb import routes
