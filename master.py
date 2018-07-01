import os
import pathlib as pl

# default subdirectory names

fdir = '/Users/jaredhand/Documents/wmwv_research/hostmass2018/Hosts_spec'
# fdir = pl.Path(os.getcwd()) / 'testdir'
fname = 'Hosts_spec'
# fname = 'testname'
dumpdir = 'dumps'
foutdir = 'fout'
specdir = 'spec'
cat_translatedir = 'cat'


class GPRMaster:
    """
    """
    def __init__(self):
        self.olddir = pl.Path(os.getcwd())
        self.fname = fname
        self.fdir = pl.Path(fdir)
        self.dumpdir = self.fdir / dumpdir

        # make directories if they do not already exist:
        self.fdir.mkdir(exist_ok=True)
        self.dumpdir.mkdir(exist_ok=True)
        



class MasterGrabber(GPRMaster):
    """
    """
    def __init__(self):
        super().__init__()
        
    

class MasterPrimer(GPRMaster):
    """
    """
    def __init__(self):
        super().__init__()


class MasterRunner(GPRMaster):
    """
    """
    def __init__(self):
        super().__init__()
