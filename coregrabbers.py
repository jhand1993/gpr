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
    in header set to json only.  This is true for anything,
    even just quereies.  No fits, no csv, or anything else.
    """
    def __init__(self):
        super().__init__()
        accept = 'application/json' # DON'T CHANGE

    def headerbuilder(self, **kwargs):
        """
        Builds and returns a header dict.  Not tested...
        """
        return dict(kwargs)
