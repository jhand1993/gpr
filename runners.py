import json
import glob
import shutil
import subprocess
import os

import pandas as pd
import numpy as np 
import primers
import grabbers
from master import MasterRunner


class FastppRunner(MasterRunner):
    """
    Contains methods to run FAST++
    """
    def __init__(self):
        super().init()

    def fastpp_runnerloop(self):
        """
        Used to loop through 
        """

        grabber = grabbers.SpectraGrabber(fname, fdir)
        grabber.spectra_grabber()
        grabber.fname
        primer = primers.FastPlusPlusPrimer(fname, fdir, binsize=10)
        primer.spec_looper()
        primer.cat_maker(ignorphot=True)
        fitslist = grabber.filelist
        paramdata = np.loadtxt(fname + '.param', dtype=str)
        paramdatadict = dict(zip(paramdata[:, 0], paramdata[:, 2]))


        def fastpp_runner(self, fits, param):
            """
            Nested function used to loop through all the files.
            """
            os.chdir(self.fdir)
            fullname = fname + '-' + fits.split('.')[0]
            paramdatadict['CATALOG'] = fullname
            with open(fullname + '.param', 'w+') as f:
                for key in list(paramdatadict.keys()):
                    value = paramdatadict[key]
                    newline = key + ' = ' + value + '\n'
                    f.write(newline)
                f.close()
            newcat = shutil.copyfile(fname + '.cat', fullname + '.cat')
            newtranslate = shutil.copyfile(
                olddir + '/' + fname + '.translate', fullname + '.translate'
                )
            cmd = 'fast++ ' + fullname + '.param'
            # shell=True is not secure at all, but will work for now
            process = subprocess.Popen(cmd, shell=True) 
            stout, sterr = process.communicate()
            process.wait()
            os.chdir(self.olddir)
        for f in fitslist:
            fastpp_runner(f, paramdata)
        grouper = primers.FastppFoutGrouper(foutdir='')
        grouper.regrouper()
        return True

    fastpp_runnerloop()
    