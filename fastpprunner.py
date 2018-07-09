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

        # This is the default fast++ command:
        if not cmd:
            self.cmd = [self.programname, self.fname + '.param']

        # if string is given as 'cmd', split it into a list:
        elif cmd and type(cmd) == str:
            self.cmd = cmd.split(' ')
        
        # otherwise, set 'cmd' to 'self.cmd':
        elif cmd :
            self.cmd = cmd
        
        # instantiate primer object as attribute:
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
                # prime data for fast++:
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

                    # 'CATALOG' key always needs to be changed.
                    paramdatadict['CATALOG'] = fullname

                    # change all .param values in new .param files specified
                    # in kwargs:
                    with open(fullname + '.param', 'w+') as f:
                        for key, value in paramdatadict.items():
                            newline = key + ' = ' + value + '\n'
                            f.write(newline)
                        f.close()
                    
                    # copy the .cat file with new file name:
                    newcat = shutil.copyfile(
                        self.fname + '.cat', 
                        fullname + '.cat'
                    )

                    # copy the .translate file with new file name:
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
                
                # make new .cat file:
                self.primer.cat_maker(includephot=includephot)
                self.runner(self.cmd)
                return True
            except Exception as e:
                print(str(e))
