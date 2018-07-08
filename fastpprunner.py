"""
Runners should not move files explicitly.  All file movement
should be done by primers and then called in the runner.
"""
import shutil
import subprocess
import os

import numpy as np 
import fastppprimer
import spectragrabber
from master import MasterRunner


class FastppRunner(MasterRunner):
    """
    Contains methods to run FAST++.
    """
    def __init__(self, cmd=None):
        super().__init__()
        self.programname = 'fast++'
        if not cmd:
            self.cmd = [self.programname, self.fname + '.param']
        elif cmd and type(cmd) == str:
            self.cmd = cmd.split(' ')
        else:
            self.cmd = cmd
        self.grabber = spectragrabber.SdssSpectraGrabber(
            specdatadir=sdssspecdatadir, 
            root=sdssroot
            )
        self.primer = fastppprimer.FastppPrimer()
        
    def fastpp_runner(self, includephot=True, includespec=True, **kwargs):
        """
        Nested function used to loop through all the files.  This will
        be rewritten with **kwargs for each parameter in .param file:

        **kwargs={param1: value1, param2: value2, ...}
        """
        os.chdir(self.fdir)
        # load .param data used by FAST++
        paramdata = np.loadtxt(self.fname + '.param', dtype=str)
        # grab .paramdata parameter:value pairs in dictionary:
        paramdatadict = dict(zip(paramdata[:, 0], paramdata[:, 2]))
        # if spectra are included, then loop through each:
        if includespec:
            try:
                self.grabber.sdss_spectra_grabber()
                self.primer.spec_looper()
                self.primer.cat_maker(includephot=includephot)
                # ftr : files to run
                self.ftrlist = self.grabber.filelist
                for f in self.ftrlist:
                    # Need to remove file extension:
                    fullname = self.fname + '-' + f.split('.')[0]
                    # make changes to .param file specificied by kwargs
                    if kwargs:
                        for key, value in kwargs.items():
                            paramdatadict[key] = value
                    # 'CATALOG' key needs to be changed.
                    paramdatadict['CATALOG'] = fullname
                    with open(fullname + '.param', 'w+') as f:
                        for key, value in paramdatadict.items():
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
                    # change self.cmd for each file fullname
                    self.cmd = [self.programname, fullname + '.param']
                    self.runner(self.cmd)
                # recombine each fast++ run on individual spectra into
                # new .fout file:
                os.chdir(self.olddir)
                grouper = fastppprimer.FastppFoutGrouper(foutdir='fout')
                grouper.regrouper()
                return True
            except Exception as e:
                print(str(e))
        else:
            try:
                # make changes to .param file specificied by kwargs
                if kwargs:
                    for key, value in kwargs.items():
                        paramdatadict[key] = value
                self.primer.cat_maker(includephot=includephot)
                self.runner(self.cmd)
                return True
            except Exception as e:
                print(str(e))
