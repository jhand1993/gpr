"""
Any file name should be attributes of a class.  Otherwise, arguments
and keyword arguments should be used in methods instead of explicit
class attributes.  If a method is used to create a file, then that
file name should instead be an argument, not an attribute.
"""
import os
import pathlib as pl
import json
import glob
import subprocess
import shutil

import requests


class GPRMaster:
    """ This is the master class for all grabbers, runners, and primers
        in the GPR framework.
    """

    def __init__(self):
        """ When initialized, configurations are loaded from master 
            configuration json file, and required subdirectores are
            made.
        """
        self._olddir = pl.Path(os.getcwd())

        # change to code directory and load masterconfig.json:
        codedir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(codedir)

        # load configuration data from master configuration:
        with open('masterconfig.json') as f:
            self._masterconfig = json.load(f)

        os.chdir(self._olddir)
        self._fname = self._masterconfig['file name']
        configfilepath = self._masterconfig['file directory']

        # handle various file directory formats for Windows/Unix-like:
        if '~' in configfilepath:
            self._fdir = pl.Path(os.path.expanduser(configfilepath))

        elif not os.path.isdir(configfilepath):
            raise Exception(configfilepath + ' is not a valid directory.')

        else:
            self._fdir = pl.Path(configfilepath)

        # Determine spectra data file type:
        if 'spectra data file type' in self._masterconfig:

            # check to see if spec file type is not blank:
            if len(self._masterconfig['spectra data file type']) == 0:
                self._specext = 'fits'

            # default to fits file otherwise:
            else:
                self._specext = self._masterconfig['spectra data file type']

        # default to fits file otherwise:
        else:
            self._specext = 'fits'


        # set file directory and dump directory as attributes:
        self._fdir = pl.Path(self._fdir)

        # make dump directory attribute:
        self._dumpdir = self._fdir / self._masterconfig['dump subdirectory name'] 

        # make dump directory if they do not already exist:
        self._dumpdir.mkdir(exist_ok=True)

        # Dump names should not change
        self._specdatadir_jd = 'specdatadir-name'
        self._fname_spec_jd = 'filename-specObjID'
        self._fname_obj_jd = 'filename-objID'
        self._specname_obj_jd = 'specname-objID'

    def _dumpmaker(self, dumpname, keys, values):
        """ Generic json dump creater.

        Args:
            dumpname (str): Name of json dump to be created.

            keys (List): List of keys for json dump data.

            values (List): List of values for json dump data.

        Returns:
            bool: True if succesful.
        """
        os.chdir(self._dumpdir)

        # create a dictionary from keys and values given:
        dumpdict = dict(zip(keys, values))

        # remove '.' from dumpname is given:
        if '.' in dumpname:
            dumpname = dumpname.split('.')[0]
        
        # save json file with dump data:
        with open(dumpname + '.json', 'w+') as f:
            json.dump(dumpdict, f)

        print(
            '\'' + dumpname + '.json\' dumped in\'',
            str(self._dumpdir) + '\'.'
        )
        os.chdir(self._olddir)
        return True

    def _dumploader(self, dumpname):
        """ Generic json dump loader.

        Args:
            dumpname (str): Name of dump to be loaded into dictionary

        Returns:
            dumpdict (Dict): Dictionary loaded from json dump.
        """
        os.chdir(self._dumpdir)

        # remove '.' from dumpname is given:
        if '.' in dumpname:
            dumpname = dumpname.split('.')[0]
        
        # load dump dictionary from json file 'dumpname':
        with open(dumpname + '.json', 'r') as f:
            dumpdict = json.load(f)

        os.chdir(self._olddir)
        return dumpdict

    def _dumpinverter(self, dump):
        """ Tries to swap dump dictionary keys and values.

        Args:
            dump (Dict[str]): Loaded json dump that is 'inverted' and
                returned as a new dictionary.

        Returns:
            dict[str]: New dictionary of inverted keys: values.
        """
        newkeys = list(dump.values())
        newvalues = list(dump.keys())

        return dict(zip(newkeys, newvalues))

        
class MasterGrabber(GPRMaster):
    """ This is the master class for all grabbers. 
    """
    def __init__(self):
        """ Initializer method for class.
        """
        super().__init__()

    def web_grabber(self, url, datadir, filelist, redownload=False):
        """ This basically works like wget or curl.  

        Args:
            url (str or List[str]): Url used to download data, or list of
                urls corresponding to each file in filelist.

            datadir (str): Subdirectory where downloaded files will be
                downloaded to.
            
            filelist (List[str]): List of file names that are downloaded
                from given url(s).

            redownload (bool): If true, then spectra data files will be
                redownloaded even if they already exist in the spectra data
                directory.  Default is False.

        Returns:
            bool: True is successful.
        """
        datadir = self._fdir / datadir

        # make datadir if it does not exist:
        datadir.mkdir(exist_ok=True)
        os.chdir(datadir)

        # grab existing files in 'datadir':
        localdata = glob.glob('*')

        # check to see if url is given as a list:
        if type(url) == list:

            # make sure that the url list is the same length as
            # the filelist:
            if len(url) != len(filelist):
                print('Url list and file list must be the same length.')
                raise ValueError

            for i in range(len(filelist)):
                # grab ith file and url:
                c_url = url[i]
                c_file = filelist[i]

                # check and skip files that are already downloaded. If
                # redownload is true, then this will be skipped:
                if c_file in localdata and not redownload:
                    print('\'' + c_file + '\' already downloaded.')

                # if they are not downloaded, then download:
                else:
                    print('Downloading \'' + c_file + '\'...')
                    r = requests.get(
                        c_url + c_file,
                        allow_redirects=True, stream=True
                        )
                    with open(c_file, 'wb') as newf:
                        shutil.copyfileobj(r.raw, newf)

        else:
            for f in filelist:
                # check and skip files that are already downloaded:
                if f in localdata:
                    print('\'' + f + '\' already downloaded.')

                # if they are not downloaded, then download:
                else:
                    print('Downloading \'' + f + '\' ...')
                    r = requests.get(
                        url + f,
                        allow_redirects=True, stream=True
                        )
                    with open(f, 'wb') as newf:
                        shutil.copyfileobj(r.raw, newf)

        os.chdir(self._olddir)
        return True
        
    
class MasterPrimer(GPRMaster):
    """ This is the master class for all primers.
    """
    def __init__(self):
        """ Initializer method for class.
        """
        super().__init__()
    
    def nm_to_mj(self, x):
        """
        Converts nanomaggies to microjanksys.

        Args: 
           x (float): Input flux in nanomaggies.

        Returns:
            float: Flux in microjanksys.
        """
        return x * 3.631


class MasterRunner(GPRMaster):
    """ This is the master class for all runners.
    """
    def __init__(self):
        """ Initializer method for class.
        """
        super().__init__()

    def runner(self, cmd):
        """ This is a wrapper for running program via subprocesses.

        Args:
            cmd (str or List[str]): If string, cmd is converted to a
                list for use in Popen instance.  Otherwise, list is
                used as command argument for Popen instance.

        Returns:
            bool: True if successfull.
        """
        try:
            # convert command string to list if needed:
            os.chdir(self._fdir)
            if type(cmd) == str:
                cmd = cmd.split(' ')

            # run the program as a subprocess:
            process = subprocess.Popen(cmd,
                shell=False
            )

            # wait for it to finish:
            process.wait()
            os.chdir(self._olddir)
            return True
        except Exception as e:
            raise
        