"""
SkyServer has a fairly unified web service for CasJobs, Skyquery,
and SkyServer, so these classes are grouped together in one file.

Take that, Jeff.

As for authorization, the token name and body format is not specified
anywhere online for SkyServer, so I had to find this on my own:

body (python dict):
{
'auth': {
    'identity': {
        'password': {
            'user': {
                'name': UserName,
                'password': Password
                }
            }
        }
    }
}

Token key: 'X-Subject-Token'

references:
http://www.sciserver.org/docs/casjobs/CasJobs_REST_API.pdf
https://media.readthedocs.org/pdf/sciserver/latest/sciserver.pdf

UPDATE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Okay so astroquery handles literally all of this apart from CasJobs.
The plan is now to integrate this project with astropy/astroquery
and hopefully develop something like an astrorunner package that will
unify Python wrapping.  This might be integrated into astroquery.
"""
import time
import json
import os
import pathlib

import numpy as np
import pandas as pd
import requests
import pypika as pp
from grabbertools import Authorize
from master import MasterGrabber


class SkyServerGrabber(MasterGrabber):
    """
    Because SkyServer shares the same login URL it makes sense
    to make all other SkyServer class.
    """
    def __init__(self, username=None, password=None):
        super().__init__()
        accept = 'application/json' # DON'T CHANGE
        username = username
        password = password
        self.tokenkey = 'X-Subject-Token'
        self.loginurl = 'https://portal.sciserver.org/login-portal/keystone/v3/tokens'
    
    def skyserv_authenticator(self):
        """
        This is the authenticator for all SkyServGrabber subclasses.
        """
        
        header = {
            'Content-Type': accept, 
            'X-Auth-Token': self.casjobtoken,
            'Accept': accept
        }
        # this format is disgusting but required....
        authdata = {
            'auth' :{
                'identity': {
                    'password': {
                        'user': {
                            'name': username,
                            'password': password
                        }
                    }
                }
            }
        }
        payload = json.dumps(authdata).encode(encoding='utf-8')
        try:
            post = requests.post(self.loginurl, data=payload, headers=header)

            if post.status_code == 200:
                response = json.loads(post.text)
                token = response[self.tokenkey]
                return token
            else:
                print('Username and/or password are invalid.')
                post.raise_for_status()
        except Exception as e:
            raise(str(e))


class SdssCasJobsGrabber(SkyServerGrabber):
    """
    Generic CasJobs grabber utilizing CasJobs API.  Each instance
    serves as a connection to the CasJobs server.  Context and Surv
    will be set at instantiation and cannot be changed (static). 
    Header will be constructed for each method. This CasJobs grabber
    is for grabbing SDSS data.
    """
    def __init__(self, context, username=None, password=None):
        super().__init__(username, password)
        context = context
        self.username = username
        self.password = password
        self.casjobsurl = 'https://skyserver.sdss.org/CasJobs/RestApi'
        self.casjobtoken = self.skyserv_authenticator()

    def jobstatus_checker(self, jobid):
        """
        Get status of a job on CasJob server
        """
        if self.casjobtoken = None:
            print('Must provide username and password to', 
            'check CasJobs job status.')
            return False
        
        header = {
            'X-Auth-Token': self.casjobtoken 
        }
        jobstatusurl = self.casjobsurl + 
        '/jobs/' + str(jobid)

        get = requests.get(jobstatusurl, headers=header)
        # return dictionary of reponse information:
        if get.status_code == 200:
            return get.headers
        else:
            get.raise_for_status()

    def quickquery_poster(self, taskname, query, usedataframe=True):
        """
        Run a quick query and convert response to pandas
        dataframe.  This is a Post.  Note that query reponse
        table is to also be json, and the keyword is 'Rows'.
        """
        tablekey = 'Rows'
        header = {
            'Content-Type': accept, 
            'X-Auth-Token': self.casjobtoken
        }

        payload = {
            'Query': query,
            'Taskname': taskname
        }
        quickqueryurl = self.casjobsurl + 
        '/contexts/' + context + '/query'
        try:
            post = requests.post(
                self.casjobsurl, 
                data=payload, headers=header, stream=True
            )
            if post.status_code == 200: 
                responsetable = post.headers[tablekey]
                if usedataframe:
                    # turn response into pandas dataframe
                    data = json.dumps(responsetable)
                    df = pd.read_json(data, orient='records')
                    return df
                else:
                    return responsetable
            else:
                post.raise_for_status()
        except Exception as e:
            print(str(e))
                
    def longquery_poster(
        self, taskname, query, 
        createtable=False, tablename=False, estimate=False,
        completequery=False, usedataframe=True
    ):
        """
        Submit a longer query that can be checked.  This is a
        Post like quickquery, but includes
        """
        if self.casjobtoken = None:
            print('Must provide username and password to', 
            'send a job to CasJobs.')
            return False

        header = {
            'Content-Type': accept,
            'X-Auth-Token': self.casjobtoken 
        }
        # Using createtable and estimate are not necessary,
        # and are not advised, but exist for full functionality:
        if not createtable and not estimate:
            payload = {
                'Query': query,
                'Taskname': taskname
            }
        elif not createtable:
            payload = {
                'Query': query,
                'Taskname': taskname,
                'Estimate': int(estimate)
            }
        elif not estimate:
            payload = {
                'Query': query,
                'Taskname': taskname,
                'CreatTable': True,
                'TableName': tablename
            }
        else:
            payload = {
                'Query': query,
                'Taskname': taskname,
                'CreatTable': True,
                'TableName': tablename,
                'Estimate': int(estimate)
            }
        longqueryurl = self.casjobsurl + 
        '/contexts/' + context + '/jobs'
        try:
            put = requests.put(
                self.casjobsurl, 
                data=payload, headers=header, stream=True
            )
            if put.status_code == 200:
                jobid = str(put.text)
                """
                responsetable = post.headers[tablekey]
                if usedataframe:
                    # turn response into pandas dataframe
                    data = json.dumps(responsetable)
                    df = pd.read_json(data, orient='records')
                    return df
                else:
                    return responsetable
                """
            else:
                put.raise_for_status()
        except Exception as e:
            print(str(e))
        # grab the results if 'completequery' is true. Because
        # context is static, the 'quickquery_poster' cannot
        # be called
        if completequery:
            # must have created table to download finished query
            if not createtable:
                print('Long query must create table to',
                'return results')
                return jobid
            else:
                while True:
                    check = self.jobstatus_checker(jobid)
                    # if the job is done, break loop
                    if check['Message'] == 'Query Complete':
                        break
                    else:
                        time.sleep(5)
                sqlquery = 'SELECT * FROM ' + tablename 
                tablekey = 'Rows'
                newheader = {
                    'Content-Type': accept, 
                    'X-Auth-Token': self.casjobtoken
                }

                newpayload = {
                    'Query': sqlquery,
                    'Taskname': 'longquerygrabber'
                }
                quickqueryurl = self.casjobsurl + 
                '/contexts/MyDB/query'
                try:
                    post = requests.post(
                        self.casjobsurl, 
                        data=newpayload, headers=newheader, stream=True
                    )
                    if post.status_code == 200: 
                        responsetable = post.headers[tablekey]
                        if usedataframe:
                            # turn response into pandas dataframe
                            data = json.dumps(responsetable)
                            df = pd.read_json(data, orient='records')
                            return df
                        else:
                            return responsetable
                    else:
                        post.raise_for_status()
                except Exception as e:
                    print(str(e))
        else:
            return jobid

    # these methods are supposed to be more user friendly, and
    # more useful for data gathering.

    def table_creater(self, tablename, columnnames, entries):
        """
        This method creats a table in the user's 'MyDB'.  As such,
        this method overrides the argument 'context'.
        """
        createrurl = self.casjobsurl + '/contexts/MyDB/query'
        

    def object_finder(
        self, datatable, objectlist, ralist, declist, radius,
        longquery=True
    ):
        """
        This method finds the nearest neighbors in a table/view called 
        'datatable' for each object in 'objectlist' within a search radius
        'radius'.
        """
        pass


class SkyQueryGrabber(SkyServerGrabber):
    """
    Generic SkyQuery grabber utilizing SkyQuery API.  This won't be
    started until astroquery format is better understood.
    """
    def __init__(self):
        super().__init__()
