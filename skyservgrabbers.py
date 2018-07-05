"""
SkyServ has a fairly unified web service for CasJobs, Skyquery,
and SkyServer, so these classes are grouped together in one file.

Take that, Jeff.
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
    def __init__(self):
        super.__init__()
        self.loginurl = 'https://portal.sciserver.org/login-portal/keystone/v3/tokens'
        


class CasJobsGrabber(RestfulGrabber):
    """
    Generic CasJobs grabber utilizing CasJobs API.  Each instance
    serves as a connection to the CasJobs server
    """
    def __init__(self, surv):
        super().__init__(username, password)
        # Login URL for all SciServer APIs
        self.surv = surv
        self.casjobtoken = self.token_getter(self.loginurl)


    def quickqueryposter(self, query, usedataframe=True):
        """
        Run a quick query and convert response to pandas
        dataframe.  This is a Post
        """

    def longqueryposter(self, query, usedataframe=True):
        """
        Submit a longer query that can be checked.  This is a
        Post.
        """

    def jobstatuschecker(self, jobid):
        """
        Get status of a query running on CasJob server
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


