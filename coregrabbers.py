"""
For uniformity, all
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
    def __init__(self, username=None, password=None):
        self.accept = 'application/json' # DON'T CHANGE
        self.auth = Authorize(username=username, password=password)

    def token_getter(self, loginurl):
        """
        Used to get token from login.
        """
        httpauth = self.auth.auth_generator()
        req = requests.get(loginurl, auth=httpauth)
        if req.status != 200:
            print('Username and/or password are invalid.')
            req.raise_for_status()
        elif req.status == 200:
            token = req.text # i think this is wrong


class CasJobsGrabber(MasterGrabber):
    """
    Generic CasJobs grabber utilizing CasJobs API.
    """
    def __init__(self, username=None, password=None):
        super().__init__(username, password)
        self.loginurl = 
        token = self.token_getter(self.loginurl)


    def quickquery(self, query, usedataframe=True):
        """
        Run a quick query and convert response to pandas
        dataframe.
        """


    
class SkyQueryGrabber(MasterGrabber):
    """
    Generic SkyQuery grabber utilizing SkyQuery API
    """
    def __init__(self):
        super().__init__()


class OACGrabber(MasterGrabber):
    """
    Grabber for the OACAPI: https://astrocats.space/ 
    """
    def __init__(self):
        super().__init__()


