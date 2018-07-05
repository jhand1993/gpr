"""
SkyServer has a fairly unified web service for CasJobs, Skyquery,
and SkyServer, so these classes are grouped together in one file.

Take that, Jeff.

As for authorization, the token name and body format is not specified
anywhere online for SkyServer, so I had to find this on my own:

body (dict):
{
'auth':{
    'identity':{
        'password':{
            'user':{
                'name':UserName,
                'password':Password
                }
            }
        }
    }
}

Token key: 'X-Subject-Token'
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
from grabbertools import Authorize
from coregrabbers import RestfulGrabber


class SkyServGrabber(RestfulGrabber):
    """
    Because SkyServer shares the same login URL it makes sense
    to make all other SkyServer class
    """
    def __init__(self, username=None, password=None):
        super.__init__(username, password)
        self.tokenkey = 'X-Subject-Token'
        self.loginurl = 'https://portal.sciserver.org/login-portal/keystone/v3/tokens'
    
    def skyserv_authenticator(self):
        """
        This is the authenticator for all SkyServGrabber subclasses.
        """
        # this format is disgusting but required....
        authdata = {
            'auth' : {
                'identity' : {
                    'password' : {
                        'user' : {
                            'name' : username,
                            'password' : password
                            }
                        }
                    }
                }
            }
        authdata_body = json.dumps(authdata).encode(encoding='utf-8')
        try:
            post = requests.post(self.loginurl, data=authdata_body)

            if post.status_code == 200:
                response = json.loads(post.text)
                token = response[self.tokenkey]
                return token
            else:
                print('Username and/or password are invalid.')
                post.raise_for_status()
        except Exception as e:
            raise(str(e))


class CasJobsGrabber(RestfulGrabber):
    """
    Generic CasJobs grabber utilizing CasJobs API.  Each instance
    serves as a connection to the CasJobs server.  Context and Surv
    will be set at instantiation and cannot be changed (static).  
    """
    def __init__(self, surv, context, username=None, password=None):
        super().__init__(username, password)
        context = context
        surv = surv
        self.casjobtoken = self.skyserv_authenticator()


    def quickquery_poster(self, query, usedataframe=True):
        """
        Run a quick query and convert response to pandas
        dataframe.  This is a Post
        """

    def longquery_poster(self, query, usedataframe=True):
        """
        Submit a longer query that can be checked.  This is a
        Post.
        """

    def jobstatus_checker(self, jobid):
        """
        Get status of a query running on CasJob server
        """

    def object_finger(
        self, datatable, objectlist, ralist, declist, radius, longquery=True
    ):
        """
        This method finds the nearest neighbors in a table/view called 
        'datatable' for each object in 'objectlist' within a search radius
        'radius'.
        """


class SkyQueryGrabber(MasterGrabber):
    """
    Generic SkyQuery grabber utilizing SkyQuery API
    """
    def __init__(self):
        super().__init__()





