import io
import os
import shutil
import json
import glob

import astropy.coordinates as apc
import astropy.units as u
import numpy as np
import pandas as pd
import tabulate as tb
import requests
from master import MasterGrabber


class SpectraGrabber(MasterGrabber):
    """
    Base class for grabbing spectra data from indiviual image/files
    for gieven targest.  
    """
    def __init__(self, specdatadir):
        super().__init__()
        self.specdatadir = self.fdir / specdatadir

        # Make specdatadir if it does not exist:
        self.specdatadir.mkdir(exist_ok=True)

        # Save 'specdatadir' into dump to be used with primer/grabber
        self.dumpmaker(
            self.specdatadir_name_jdump, 
            [self.specdatadir_name_jdump], 
            [specdatadir]
        )
        self.filelist = []
        self.df = pd.DataFrame()
        try:

            # try to make pandas dataframe from file 'fname':
            os.chdir(self.fdir)
            self.df = pd.read_csv(self.fname + '.csv', dtype=str)
            os.chdir(self.olddir)
        except FileNotFoundError as e:
            print(
                'FileNotFoundError: ' + fname +
                '.csv not found in ' + self.fdir + '.'
            )
            raise
        finally:
            os.chdir(self.olddir)

    def df_getter(self):
        """
        Prints and returns the dataframe 'self.df'.
        """
        print(self.df)
        return self.df


class SdssSpectraGrabber(SpectraGrabber):
    """
    Inherits from 'SpectraGrabber', but tailored for grabbing data from
    SDSS SAS.  Can be used to grab spectra from mjd, place, fiberID information
    from a valid data file/table.  
    """
    def __init__(self, specdatadir, dr, url):
        super().__init__(specdatadir)
        self.url = url
        self.dr = dr

    def sdss_spectra_grabber(self):
        """
        Grabs spectra data from SDSS DR14 from given datafram df.  df should
        have 'mjd', 'plate', and 'fiberID' information. 'jsondump' creates
        and stores dictionaries of specObjID:objID pairs and
        specObjID:fits-file pairs for use creating spectra table for FAST++
        during priming.
        """
        specObjIDlist = []
        objIDlist = []
        specnamelist = []
        os.chdir(self.fdir)
        try:

            # try and grab the necessary columns from 'df'
            mjds = np.array(self.df['mjd'], dtype=str)
            plates = np.array(self.df['plate'], dtype=str)
            fiberIDs = np.array(self.df['fiberID'], dtype=str)
            specObjIDlist = list(self.df['specObjID'])
            objIDlist = list(self.df['objID'])
        except KeyError as k:
            print(k)
            print('Make sure downloaded data contains required columns.')
            return False
        except:
            raise
        rowcount = self.df.shape[0]

        # will be ued soon
        ebosslist = []
        sdsslist = []
        try:
            os.chdir(self.specdatadir)
            localspecdata = glob.glob('*.fits')
            if len(localspecdata) == rowcount:
                print(
                    'Fits files already downloaded in directory \'' +
                    str(self.specdatadir) + '\''
                )
                self.filelist = glob.glob('*.fits')
                os.chdir(self.olddir)
                return True
            else:
                print(
                    'Downloading spectra from \'' + self.url + '\'...'
                )
                for row in range(rowcount):

                    # run through the rows of the df, construct file name,
                    # determine if spectra is from legacy or from eboss,
                    # and download file via requests.get() after constructing URL.
                    # See http://www.sdss.org/dr14/data_access/bulk/ for more
                    # information.
                    plate = plates[row]
                    mjd = mjds[row]
                    fiberID = fiberIDs[row]
                    if int(plate) < 3006:

                        # for older spectra
                        suburl = 'sdss/spectro/redux/26/spectra/'
                    else:

                        # for newer spectra
                        suburl = 'eboss/spectro/redux/v5_10_0/spectra/'
                    plate = str(plate)
                    if len(plate) < 4:

                        # 'plate' is stored as an int, but the 'plate' portion of
                        # the fits file name is a string of length 4, so zeroes may
                        # need to be added to 'plate'.
                        while len(plate) < 4:
                            plate = '0' + plate
                    if len(fiberID) < 4:

                        # 'fiberID' is stored as an int, but the 'fiberID' portion
                        # of the fits file name is a string of length 4, so zeroes
                        # may need to be added to 'fiberID'.
                        while len(fiberID) < 4:
                            fiberID = '0' + fiberID
<<<<<<< HEAD
                    
                    # create url that is used to download file"
                    url = self.url + suburl + plate + '/'

                    # create file name for file that is to be downloaded:
=======
                    url = self.url + suburl + plate + '/'
>>>>>>> 0a3bbc6c2a14188a294fd37789610624f67c2685
                    specname = 'spec-' + plate + '-' + mjd + '-' + fiberID + '.fits'
                    if specname in localspecdata:
                        print('\'' + specname + '\' already downloaded.')
                    else:
                        print('Downloading \'' + specname + '\'...')
                        r = requests.get(
                            url + specname, allow_redirects=True, stream=True
                            )
                        with open(specname, 'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                    specnamelist.append(specname)
                self.filelist = specnamelist
                print('Done.')

                # create dumps related filenames to specObjID and objID:
                self.dumpmaker(self.fname_spec_jdump, specnamelist, specObjIDlist)
                self.dumpmaker(self.fname_obj_jdump, specnamelist, objIDlist)
                os.chdir(self.olddir)
                return True
        except Exception as e:
            print(str(e))
            raise
        finally:
            os.chdir(self.olddir)
            