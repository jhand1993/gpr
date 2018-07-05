"""
This will be the grabber for the OAC API schema:
https://github.com/astrocatalogs/schema

This API has really doesn't require authentication as the
data is stored in public github repositories.  That should
make life easier.
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


class OACGrabber(MasterGrabber):
    """
    Grabber for the OACAPI: https://astrocats.space/ 
    """
    def __init__(self):
        super().__init__()