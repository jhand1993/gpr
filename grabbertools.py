"""
These classes and functions are used for authentication 
for web services such as CasJobs API and so on.  No actual
HTTP methods are to be used here.

SQL query constuctors will be included here as well.

For readability and generality, request.auth.HTTPBasicauth is
to be used instead of the 'auth' tuple keyword.
"""

import json
import os
import pathlib
import shutil
import io
import glob
import getpass

import numpy as np
import pandas as pd
import requests.auth as auth
import urllib3
from master import MasterGrabber


class Authorize:
    """
    This class contains username and password used for authorization
    via API.  
    """
    def __init__(self, username=None, password=None):
        """
        By default, the user provides credentials for authentication.
        Otherwise one can specifcy the username and password 
        explicitly.
        """
        if not username:
            self.username = getpass.getuser()
        else:
            self.username = username
        
        if not password:
            self.password = getpass.getpass()
        else:
            self.username = password

    def auth_generator(self):
        """
        returns HTTPBasicauth for 'username' and 'password' attributes.
        """
        return auth.HTTPBasicAuth(self.username, self.password)


class Token:
    """
    This class is the token returned from HTTP authorization.
    """
    def __init__(self, token):
        self.token = token

