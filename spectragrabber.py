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
    def __init__(self, specdatadir, filename=None):
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

            # try to make pandas dataframe from file 'fname'.
            # If 'filename' is None, then use self.fname + .csv:
            os.chdir(self.fdir)
            if not filename:
                self.df = pd.read_csv(self.fname + '.csv', dtype=str)

            # make sure there is an extension in 'filename':
            elif '.' not in filename:
                e = 'No file extension given for given filename.'
                raise Exception(e)
            else:

                # check to make sure 'filename' exists
                actualfile = glob.glob(filename)
                if len(actualfile) == 0:
                    e = filename + ' not found in ' + self.fdir + '.'
                    raise FileNotFoundError(e)
                
                # fine extension and load data appropriately:
                ext = filename.split('.')[0]
                if ext == '.csv':
                    self.df = pd.read_csv(filename, dtype=str)
                elif ext == '.tsv':
                    self.df = pd.read_csv(filename, dtype=str, delimiter='\t')
                elif ext == '.txt':
                    self.df = pd.read_csv(
                        filename, dtype=str, delimiter_whitespace=True
                    )
                else:
                    
                    # tell them to use a different ext...
                    raise Exception('Use a different file extension.')
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
    def __init__(self, specdatadir, url):
        super().__init__(specdatadir)
        self.url = url

    def sdss_spectra_grabber(self):
        """
        Grabs spectra data from SDSS DR14 from given datafram df.  df should
        have 'mjd', 'plate', and 'fiberID' information. 'jsondump' creates
        and stores dictionaries of specObjID:objID pairs and
        specObjID:fits-file pairs for use creating spectra table for FAST++
        during priming.
        """
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

        # 'rowcount' corresponds to the number of files to be
        # downloaded:
        rowcount = self.df.shape[0]

        # used to store separate file/url names
        ebosslist = []
        sdsslist = []
        ebossurllist = []
        sdssurllist = []
        specnamelist = []

        # grab existing spectra files:
        os.chdir(self.specdatadir)
        localfiles = glob.glob('*')

        for i in range(rowcount):

            # grab ith values from arrays:
            mjd = mjds[i]
            plate = plates[i]
            fiberID = fiberIDs[i]

            # skip rows that do not have spectra data:
            if 'nan' in str(specObjIDlist[i]) or int(mjd) <= 0:
                pass
            else:
                try:

                    # 'plate' is stored as an int, but the 'plate' portion of
                    # the fits file name is a string of length 4, so zeroes may
                    # need to be added to 'plate'.
                    if len(plate) < 4:
                        while len(plate) < 4:
                            plate = '0' + plate

                    # 'fiberID' is stored as an int, but the 'fiberID' portion
                    # of the fits file name is a string of length 4, so zeroes
                    # may need to be added to 'fiberID'.                      
                    if len(fiberID) < 4:
                        while len(fiberID) < 4:
                            fiberID = '0' + fiberID
                    
                    # create spectra file name:
                    joinlist = ['spec', plate, mjd, fiberID]
                    specname = '-'.join(joinlist) + '.fits'

                    # append spectra file name to specnamelist:
                    specnamelist.append(specname)

                    # for older spectra:
                    if int(plate) < 3006:
                        suburl = 'sdss/spectro/redux/26/spectra/'

                        # create url that is used to download file"
                        url = self.url + suburl + plate + '/'
                        sdsslist.append(specname)
                        sdssurllist.append(url)

                    # for newer spectra:
                    else:
                        suburl = 'eboss/spectro/redux/v5_10_0/spectra/'

                        # create url that is used to download file"
                        url = self.url + suburl + plate + '/'
                        ebosslist.append(specname)
                        ebosslist.append(url)
                except Exception as e:
                    raise
        
        os.chdir(self.olddir)

        # grab the spectra data:
        self.web_grabber(ebossurllist, self.specdatadir, ebosslist)
        self.web_grabber(sdssurllist, self.specdatadir, sdsslist)

        # create dumps related filenames to specObjID and objID:
        self.dumpmaker(self.fname_spec_jdump, specnamelist, specObjIDlist)
        self.dumpmaker(self.fname_obj_jdump, specnamelist, objIDlist)
        
        return True
