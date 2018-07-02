import shutil
import subprocess
import os

import numpy as np 
import primers
import grabbers
from master import MasterRunner

sdssroot = 'https://data.sdss.org/sas/dr14/'
sdssspecdatadir = 'specdata'


class FastppRunner(MasterRunner):
    """
    Contains methods to run FAST++.
    """
    def __init__(self):
        super().__init__()
        self.grabber = grabbers.SdssSpectraGrabber(
            specdatadir=sdssspecdatadir, 
            root=sdssroot
            )
        self.primer = primers.FastppPrimer()
        
    def fastpp_runner(self, **kwargs):
        """
        Nested function used to loop through all the files.  This will
        be rewritten with **kwargs for each parameter in .param file:

        **kwargs={param1: value1, param2: value2, ...}
        """
        self.grabber.sdss_spectra_grabber()
        self.primer.spec_looper()
        self.primer.cat_maker(ignorphot=False)
        self.ftrlist = self.grabber.filelist
        # ftr : files to run
        os.chdir(self.fdir)
        # load .param data used by FAST++
        paramdata = np.loadtxt(self.fname + '.param', dtype=str)
        # grab .paramdata parameter:value pairs in dictionary:
        paramdatadict = dict(zip(paramdata[:, 0], paramdata[:, 2]))
        print(self.ftrlist)
        for f in self.ftrlist:
            # Need to remove file extension:
            fullname = self.fname + '-' + f.split('.')[0]
            if kwargs:
                for key, value in kwargs.items():
                    paramdatadict[key] = value
            paramdatadict['CATALOG'] = fullname
            with open(fullname + '.param', 'w+') as f:
                for key, value in paramdatadict.items():
                    # value = paramdatadict[key]
                    newline = key + ' = ' + value + '\n'
                    f.write(newline)
                f.close()
            newcat = shutil.copyfile(
                self.fname + '.cat', 
                fullname + '.cat'
            )
            newtranslate = shutil.copyfile(
                self.fname + '.translate', 
                fullname + '.translate'
            )
            cmd = 'fast++ ' + fullname + '.param'
            # shell=True is not secure at all, but will work for now
            process = subprocess.Popen(cmd, shell=True) 
            # stout, sterr = process.communicate()
            process.wait()
        os.chdir(self.olddir)
        grouper = primers.FastppFoutGrouper(foutdir='fout')
        grouper.regrouper()
        return True

x = FastppRunner()
x.fastpp_runner()
