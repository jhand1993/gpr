import os
import pathlib as pl
import json
import glob
import subprocess

import requests


class GPRMaster:
    """
    This is the master class for all classes in GPR.
    Includes json dump methods to handle data sharing
    between different grabbers, primers, and runners.

    !!! Decision has been made to not rely on astropy
    for unit conversion or calculations. !!!
    """
    def __init__(self):
        self.olddir = pl.Path(os.getcwd())

        # change to code directory and load masterconfig.json:
        codedir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(codedir)

        # load configuration data from master configuration:
        with open('masterconfig.json') as f:
            masterconfig = json.load(f)
            f.close
        os.chdir(self.olddir)
        self.fname = masterconfig['file name']
        configfilepath = masterconfig['file directory']

        # handle various file directory formats.
        if '~' in configfilepath or '~user' in configfilepath:
            self.fdir = pl.Path(os.path.expanduser(configfilepath))
        elif not os.path.isdir(configfilepath):
            raise Exception(configfilepath + ' is not a valid directory.')
        else:
            self.fdir = pl.Path(configfilepath)

        # set file directory and dump directory as attributes:
        self.fdir = pl.Path(fdir)
        self.dumpdir = self.fdir / masterconfig['dump subdirectory name']

        # make dump directory if they do not already exist:
        self.dumpdir.mkdir(exist_ok=True)

        # Dump names should not change
        self.specdatadir_name_jdump = 'specdatadir-name'
        self.fname_spec_jdump = 'filename-specObjID'
        self.fname_obj_jdump = 'filename-objID'
        self.fullname_obj_jdump = 'fullname-objID'

    def dumpmaker(self, dumpname, keys, values):
        """
        Generic json dump creater.
        """
        os.chdir(self.dumpdir)

        # create a dictionary from keys and values given:
        dumpdict = dict(zip(keys, values))

        # remove '.' from dumpname is given:
        if '.' in dumpname:
            dumpname = dumpname.split('.')[0]
        
        # save json file with dump data:
        with open(dumpname + '.json', 'w+') as f:
            json.dump(dumpdict, f)
            f.close()
        print(
            '\'' + dumpname + '.json\' dumped in\'',
            str(self.dumpdir) + '\'.'
        )
        os.chdir(self.olddir)
        return True

    def dumploader(self, dumpname):
        """
        Generic json dump loader.
        """
        try:
            os.chdir(self.dumpdir)

            # remove '.' from dumpname is given:
            if '.' in dumpname:
                dumpname = dumpname.split('.')[0]
            
            # load dump dictionary from json file 'dumpname':
            with open(dumpname + '.json', 'r') as f:
                dumpdict = json.load(f)
            os.chdir(self.olddir)
            return dumpdict
        except Exception as e:
            print(str(e))

        
class MasterGrabber(GPRMaster):
    """
    This is the master class for all grabbers. 
    """
    def __init__(self):
        super().__init__()

    def web_grabber(self, url, datadir, filelist):
        """
        This basically works like wget or curl.  This method
        is just a generic file downloader that iterates through
        'filelist' and downloads each file from 'url' to 'datadir'.
        """
        datadir = self.fdir / datadir

        # make datadir if it does not exist:
        datadir.mkdir(exist_ok=True)
        os.chdir(datadir)

        # grab existing files in 'datadir':
        localdata = glob.glob('*')
        for f in filelist:
            try:
                # check and skip files that are already downloaded:
                if f in localdata:
                    print('\'' + f + '\' already downloaded.')

                # if they are not downloaded, then download:
                else:
                    print('Downloading \'' + specname + '\'...')
                    r = requests.get(
                        url + f, allow_redirects=True, stream=True
                        )
                    with open(f, 'wb') as newf:
                        shutil.copyfileobj(r.raw, newf)
                        newf.close()
            except Exception as e:
                print(str(e))
        os.chdir(self.olddir)
        return True
        
    
class MasterPrimer(GPRMaster):
    """
    This is the master class for all primers.
    """
    def __init__(self):
        super().__init__()
    
    def nm_to_mj(self, x):
        """
        Converts nanomaggies to microjanksys.
        """
        return x * 3.631


class MasterRunner(GPRMaster):
    """
    This is the master class for all runners.
    """
    def __init__(self):
        super().__init__()

    def runner(self, cmd):
        """
        This is a wrapper or opening a pipe via subprocess. The
        input 'cmd' and be either a shell command or, preferably,
        a list containing the command and parameters.
        """
        try:
            # convert command string to list if needed:
            os.chdir(self.fdir)
            if type(cmd) == str:
                cmd = cmd.split(' ')

            # run the program as a subprocess:
            process = subprocess.Popen(cmd,
                shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )

            # wait for it to finish:
            process.wait()
            os.chdir(self.olddir)
            return True
        except Exception as e:
            print(str(e))
            raise
        