from flask import Flask, render_template, request, make_response, redirect
from bs4 import BeautifulSoup as bs

import requests
import time
import json

from . import api

from .. import db
from .. import util
from .. import auth
from .. import variables
from .. import exceptions

@api.route("/v1/cookie")
def api_v1_get_cookie():
    try:
        verified = auth.auth_credentials(request)
    except exceptions.AuthError:
        return 