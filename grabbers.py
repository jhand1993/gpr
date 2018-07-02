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


class OscConnection:
    """ 
    Opens and maintains a connection to osc for grabbing data.
    !!! Needs to be integrated into MasterGrabber class !!!
    """
    def __init__(self, fname='payload.param'):
        self.surv = ''
        self.req = ''
        self.reqexists = False # Gets set to true when self.reqexists is populated.
        self.json = ''
        self.header = ''
        self.scope = ''
        self.table = ''
        self.df = pd.DataFrame()
        self.tableexistence = False # Gets set to true when self.table is populated.
        self.header = []
        self.catalogdomain = 'https://api.sne.space/'
        self.path = self.catalogdomain
        self.payloadname = fname
        try:
            # Create payload when instantiating:
            p = np.genfromtxt(self.payloadname, dtype=str, delimiter=';;')
            plist= list(zip(p[:,0], p[:,1]))
            if 'format' not in list(sum(plist, ())):
                plist.append(('format', 'tsv'))
            self.payload = plist
            table = tb.tabulate(self.payload, headers=['Name', 'Value'])
            print('Payload:')
            print(table) 
        except:
            raise          

    def scope_setter(self, scope):
        """ Sets the scope of the REST API 'get' call. """
        self.scope = scope
        self.path = self.catalogdomain + scope
        print('Scope:', scope)
        return True

    def payload_maker(self):
        """
        Creates a dictionary of name:value pairs that are passed to osc.
        Name:value pairs are taken from from fname.  Delimiter must be ';;'.
        """
        p = np.genfromtxt(self.payloadname, dtype=str, delimiter=';;')
        plist= list(zip(p[:,0], p[:,1]))
        if 'format' not in list(sum(plist, ())):
            plist.append(('format', 'tsv'))
        self.payload = plist
        table = tb.tabulate(self.payload, headers=['Name', 'Value'])
        print('Payload:')
        print(table)
        return True

    def get_payload(self):
        """
        Prints payload provided in payload.tsv.  If 'grabber' is called,
        then something???????
        """
        table = tb.tabulate(self.payload, headers=['Name', 'Value'])
        print('Payload:')
        print(table)
        return True

    def grabber(self):
        """
        Grabs and returns data from osc given payload parameters.  Note that
        the data is grabbed via https using a REST API called OACAPI.
        """
        self.req = requests.get(self.path, params=self.payload)
        self.reqexists = True
        print('url:', self.req.url)
        return self.req


    def table_maker(self, coordunits='deg', surv=None):
        """
        Creates and returns a Pandas dataframe and a numpy array containing
        data retrieved from 'OscConnection.grabber()'
        """
        if not self.reqexists:
            print('Running method \'grabber\'...')
            self.req = requests.get(self.path, params=self.payload)
            self.reqexists = True
            print('url:', self.req.url)
        self.surv = surv
        if surv != None:
            print()
            print('No \'Surv\' column will be added.')
            print()
        elif type(surv) != str:
            print()
            print('\'Surv\' column will not be added.  Surv must be a string!')
            print()
            surv = None
        else:
            try:
                data = io.StringIO(self.req.text)
                self.df = pd.read_csv(data, delimiter='\t')
                if self.df.empty:
                    print('No data retrieved.')
                    return False
                elif coordunits == 'deg':
                    dnarr = np.array([list(x) for x in self.df.values])
                    self.header = list(self.df.columns)
                    ra_ind = self.header.index('ra')
                    dec_ind = self.header.index('dec')
                    for i in range(len(dnarr[:,0])):
                        # get rid of the initial "
                        dnarr[i, 0] = dnarr[i, 0].replace('"', '')
                        ra = str(np.copy(dnarr[i,ra_ind])).split(',')[0]
                        dec = str(np.copy(dnarr[i,dec_ind])).split(',')[0]
                        coord = apc.SkyCoord(
                            ra + ' ' + dec, unit=(u.hourangle, u.deg)
                            )
                        dnarr[i,ra_ind] = str(coord.ra.degree)
                        dnarr[i,dec_ind] = str(coord.dec.degree)
                    if surv != None:
                        self.header.append('Surv')
                        dnlen = len(dnarr[:, 0])
                        sarr = np.full(dnlen, surv)[np.newaxis].T
                        dnarr = np.concatenate((dnarr, sarr), axis=1)
                else:
                    dnarr = np.array([list(x) for x in self.df.values])
                    header = list(self.df.columns)
                    for i in range(len(dnarr[:,0])):
                        # get rid of the initial "...
                        dnarr[i,0] = dnarr[i,0].replace('"', '')
                    if surv != None:
                        self.header.append('Surv')
                        dnlen = len(dnarr[:, 0])
                        sarr = np.full(dnlen, surv)[np.newaxis].T
                        dnarr = np.concatenate((dnarr, sarr), axis=1)
                self.table = dnarr
                self.tableexistence = True
                print(self.table)
                self.df = pd.DataFrame(data=self.table, columns=self.header)
                print(self.df)
                return self.table, self.df
            except:
                raise

    def xlink_cutter(self, photo=5, spectra=5):
        """
        Cuts out photolink and spectralink values less than those given by
        parameters 'photo' and 'spectra.'
        """
        bad = []
        ldic = {'photolink': photo, 'spectralink': spectra}
        if not self.tableexistence:
            print('Table has not been created.')
            return False
        else:
            # get rid of ldic keys that are not in header.
            for i in range(len(ldic.keys())):
                key = list(ldic.keys())[i]
                if key not in self.header:
                    ldic.pop(key)
                else:
                    pass
            for l in list(ldic.keys()):
                lindex = self.header.index(l)
                for i in range(len(self.table[:, 0])):
                    datapoints = str(self.table[i, lindex]).split(',')
                    if len(datapoints) == 1:
                        bad.append(i)
                    elif int(datapoints[0]) < ldic[l]:
                        bad.append(i)
                    else:
                        pass
            self.df = self.df.drop(bad, axis=0)
            self.table = np.array([list(x) for x in self.df.values])
            return True


    def get_table(self):
        """
        Prints the dataframe 'self.df' of the grabbed data.  The dataframe is
        formatted as human-friendly table, so it is printed instead of
        'self.table'.
        """
        if not self.tableexistence:
            print('Table has not been created.')
            return False
        else:
            print(self.df)
            return True


    def fmaker_tsv(self, fname, comments='#', path=os.getcwd()):
        """
        Creates a tab-separated data file with name 'fname'.
        'OscConnection.get_table()' needs to be ran before file can be made.
        """
        if not self.tableexistence:
            print('Need to have a populated data table before creating output file.')
            return False
        else:
            np.savetxt(fname, self.table,
                              header='\t'.join(self.header),
                              fmt='%s', comments=comments, delimiter='\t')
            return True


class SpectraGrabber(MasterGrabber):
    """
    Used to grab SDSS spectra from mjd, place, fiberID information found
    in downloaded sql query.
    """
    def __init__(self, specdatadir):
        super().__init__()
        self.specdatadir = self.fdir / specdatadir
        # Make specdatadir if it does not exist:
        self.specdatadir.mkdir(exist_ok=True)
        # Save 'sepcdatadir' into dump to be used with primer/grabber
        self.dumpmaker(
            self.specdatadir_name_jdump, 
            [self.specdatadir_name_jdump], 
            [specdatadir]
        )
        self.filelist = []
        self.df = pd.DataFrame()
        try:
            # try to make pandas dataframe from file 'fname'
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
    def __init__(self, specdatadir, root):
        super().__init__(specdatadir)
        self.root = root

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
                    'Downloading spectra from \'' + self.root + '\'...'
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
                        subroot = 'sdss/spectro/redux/26/spectra/'
                    else:
                        # for newer spectra
                        subroot = 'eboss/spectro/redux/v5_10_0/spectra/'
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
                    url = self.root + subroot + plate + '/'
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
                self.dumpmaker(self.fname_spec_jdump, specnamelist, specObjIDlist)
                self.dumpmaker(self.fname_obj_jdump, specnamelist, objIDlist)
                os.chdir(self.olddir)
                return True
        except Exception as e:
            print(str(e))
            raise
        finally:
            os.chdir(self.olddir)
            