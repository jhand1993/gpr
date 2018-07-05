"""
First and foremost, I am aware that having so many classes in 
one file is bad form, but these are so fundamental to grabbing
astronomy/cosmology data that one can argue otherwise
"""

import json
import os
import pathlib
import shutil
import io
import glob

import astropy.coordinates as apc
import astropy.units as u
import numpy as np
import pandas as pd
import requests
import urllib3
from grabbertools import Authorize, Token
from master import MasterGrabber


class RestfulGrabber(MasterGrabber):
    """
    Base REST API grabber class.  Used to keep 'Accept'
    in header set to json only.  No fits.
    """
    def __init__(self):
        super().__init__()
        self.accept = 'application/json' # DON'T CHANGE

    def token_getter(self, loginurl, username=None, password=None):
        """
        This gets a token given a login URL, username, and password.
        """
        auth = Authorize(username=username, password=password)
        httpauth = self.auth.auth_generator()
        req = requests.get(loginurl, auth=httpauth)
        if req.status != 200:
            print('Username and/or password are invalid.')
            req.raise_for_status()
        elif req.status == 200:
            response = json.loads(req.text)
            token = X‐Auth‐Token # i think this is wrong

    def headerbuilder(self, **kwargs):
        """
        Builds and returns a header dict.  Not tested...
        """
        return dict(kwargs)
