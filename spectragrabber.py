import io
import os
import shutil
import json
import glob

import numpy as np
import pandas as pd
from master import MasterGrabber


class SpectraGrabber(MasterGrabber):
    """ Base class for grabbing spectra data from indiviual image/files
        for given targest.  
    """
    def __init__(self, specdatadir, filename=None):
        """ Initializer method for class.

        Args:
            specdatadir (str): Spectra data directory that spectra data files
                will be downloaed to.
            
            filename (str): User can provide a file containing information
                needed to construct spectra data file names.  
        """
        super().__init__()
        self._specdatadir = self._fdir / specdatadir

        # Make _specdatadir if it does not exist:
        self._specdatadir.mkdir(exist_ok=True)

        # Save '_specdatadir' into dump to be used with primer/grabber
        self._dumpmaker(
            self._specdatadir_jd, 
            [self._specdatadir_jd], 
            [specdatadir]
        )
        self.filelist = []
        self.df = pd.DataFrame()
        # try to make pandas dataframe from file '_fname'.
        # If 'filename' is None, then use self._fname + .csv:
        os.chdir(self._fdir)
        if not filename:
            self.df = pd.read_csv(self._fname + '.csv', dtype=str)

        # make sure there is an extension in 'filename':
        elif '.' not in filename:
            message = 'No file extension given for given filename.'
            raise Exception(message)
        else:

            # check to make sure 'filename' exists
            actualfile = glob.glob(filename)
            if len(actualfile) == 0:
                message = filename + ' not found in ' + self._fdir + '.'
                raise FileNotFoundError(message)
            
            # fine extension and load data appropriately:
            ext = filename.split('.')[0]

            if ext == 'csv':
                self.df = pd.read_csv(filename, dtype=str)

            elif ext == 'tsv':
                self.df = pd.read_csv(filename, dtype=str, delimiter='\t')

            elif ext == 'txt':
                self.df = pd.read_csv(
                    filename, dtype=str, delimiter_whitespace=True
                )

            elif ext == 'json':
                self.df = pd.read_json(filename, dtype=str)

            else:
                # tell them to use a different ext...
                raise Exception('Invalid file extension.')

        # Make the dataframe columns lowercase:
        self.df.columns = [str(col).lower() for col in list(self.df.columns)]
        
        os.chdir(self._olddir)

    def df_getter(self):
        """ Prints and returns the dataframe 'self.df'.

        Returns:
            DataFrame: Returns the dataframe created during 
                instantiation.
        """
        print(self.df)
        return self.df


class SdssSpectraGrabber(SpectraGrabber):
    """ Used for grabbing data (such as fits files) from SDSS SAS.  
    """

    def __init__(self, specdatadir):
        """ Initializer method for class.

        Args:
            specdatadir (str): Spectra data directory that spectra data files
                will be downloaed to.
        """
        
        if self._specext != 'fits':
            raise Exception('SDSS spectra data is saved in fits file.')
        super().__init__(specdatadir)

    def sdss_spectra_grabber(
        self, url, 
        specidcol=None, photoidcol=None, include_photoid=True, redownload=False
    ):
        """ Builds sdss spectra data file names from data file and downloads 
            cooresponding spectra files form SDSS.

        Args:
            url (str): SAS url for downloading fits files.

            specidcol (str): If provided, this string represents the spectra data
                column that uniquely idenfifies the object.  If None, then the column
                name will be set to 'specObjID'. Default is None.

            photoidcol (str): Similar to specidcol argument, but instead should be
                the column that uniquely identifies the photometric data of the object.
                If None, then column name will be 'objID'.  Default is None.

            include_photoid (bool): If False, then the photometry data identification
                column is ignored (even if explicitly provided).  The json dump
                relating photometric identifier to the spectra data file name will
                not be created, which means the resulting downloaded data cannot be
                used with the FastppPrimer class.  Default is True.

            redownload (bool): If true, then spectra data files will be
                redownloaded even if they already exist in the spectra data
                directory.  Default is False.

        Returns:
            bool: True if successful.
        """

        # Set the spectra object ID column name:
        if specidcol:
            specobjidcol = specidcol.lower()
        
        else:
            specobjidcol = 'specobjid'

        # Set the object ID column name
        if photoidcol and include_photoid:
            objidcol = photoidcol.lower()

        else:
            objidcol = 'objid'

        # used to store separate file/url names:
        ebosslist = []
        sdsslist = []
        ebossurllist = []
        sdssurllist = []
        specfilelist = []
        newspecobjidlist = []
        newobjidlist = []

        # grab existing spectra files:
        os.chdir(self._specdatadir)

        for index, row in self.df.iterrows():

            # Grab the data from each row that will be needed:
            mjd = str(row['mjd'])
            plate = str(row['plate'])
            fiberid = str(row['fiberid'])
            specobjid = str(row[specobjidcol])
            if include_photoid:
                objid = str(row[objidcol])

            # skip objects with no spectra:
            if 'nan' in specobjid or int(mjd) <= 0:
                pass
            
            else:
                # Add valid objid and specobjid to their respetive new list so
                # that the correct identifiers are provided for each spectra:
                newspecobjidlist.append(specobjid)
                if include_photoid:
                    newobjidlist.append(objid)

                # 'plate' and 'fiberid need zeroes added sometimes:
                plate = plate.zfill(4)
                fiberid = fiberid.zfill(4) 

                # create spectra data file name:
                joinlist = ['spec', plate, mjd, fiberid]
                specfile = '-'.join(joinlist)

                # append spectra file name to specnamelist:
                specfilelist.append(specfile)

                # for older spectra:
                if int(plate) < 3006:
                    suburl = 'sdss/spectro/redux/26/spectra/'

                    # create url that is used to download file"
                    fileurl = url + suburl + plate + '/'
                    sdsslist.append(specfile + self._specext)
                    sdssurllist.append(fileurl)

                # for newer spectra:
                else:
                    suburl = 'eboss/spectro/redux/v5_10_0/spectra/'

                    # create url that is used to download file"
                    fileurl = url + suburl + plate + '/'
                    ebosslist.append(specfile + self._specext)
                    ebossurllist.append(fileurl)
        
        os.chdir(self._olddir)

        # grab the spectra data:
        self.web_grabber(
            ebossurllist, self._specdatadir, ebosslist, redownload=redownload
        )
        self.web_grabber(
            sdssurllist, self._specdatadir, sdsslist, redownload=redownload
        )

        # create dumps related filenames to specobjid and objid:
        self._dumpmaker(self._fname_spec_jd, specfilelist, newspecobjidlist)

        # only include objid dump if requested:
        if include_photoid:
            self._dumpmaker(self._fname_obj_jd, specfilelist, newobjidlist)
        
        return True
