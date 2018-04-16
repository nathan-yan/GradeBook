from flask import Flask, render_template, request, make_response, redirect
from bs4 import BeautifulSoup as bs

import requests
import time
import json

from . import home

from .. import db
from .. import util
from .. import auth
from .. import variables
from .. import exceptions

@home.route("/chat", methods = ['POST'])
def show_chat():
    
    return render_template("misc/deleted.html")

@home.route("/info/data", methods = ['GET'])
def show_info():
    return render_template("home/chat_template.html")

