"""
These classes and functions are used for authentication 
for web services such as CasJobs API and so on.  No actual
HTTP methods are to be used here.

For readability and generality, request.auth.HTTPBasicauth is
to be used instead of the 'auth' tuple keyword.
"""
import getpass

import requests.auth as auth


class Authorize:
    """
    This class contains username and password used for authorization
    via API.  Only used for SDSS CasJobs.
    """
    def __init__(self, username=None, password=None):
        """
        By default, the user provides credentials for authentication.
        Otherwise one can specify the username and password 
        via the relatively secure getpass module.
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
