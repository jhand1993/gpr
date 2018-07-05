import os
import pathlib as pl
import json

# default subdirectory names

# fdir = '/Users/jaredhand/Documents/wmwv_research/hostmass2018/Hosts_spec'
# fdir = pl.Path(os.getcwd()) / 'testdir'
# fname = 'Hosts_spec'
# fname = 'testname'
fdir = '/Users/jaredhand/Documents/wmwv_research/hostmass2018/starlight'
fname = 'starlight'
dumpdir = 'dumps'
foutdir = 'fout'
specdir = 'spec'
cat_translatedir = 'cat'


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
        self.fname = fname
        self.fdir = pl.Path(fdir)
        self.dumpdir = self.fdir / dumpdir
        # Dump names should not change
        self.specdatadir_name_jdump = 'specdatadir-name'
        self.fname_spec_jdump = 'filename-specObjID'
        self.fname_obj_jdump = 'filename-objID'
        # make directories if they do not already exist:
        self.fdir.mkdir(exist_ok=True)
        self.dumpdir.mkdir(exist_ok=True)

    def dumpmaker(self, dumpname, keys, values):
        """
        Generic json dump creater.
        """
        os.chdir(self.dumpdir)
        dumpdict = dict(zip(keys, values))
        if '.' in dumpname:
            dumpname = dumpname.split('.')[0]
        with open(dumpname + '.json', 'w+') as f:
            json.dump(dumpdict, f)
            f.close()
        print(
            '\'' + dumpname + '.json\' dumped in\'',
            str(self.dumpdir) + '\''
        )
        os.chdir(self.olddir)
        return True

    def dumploader(self, dumpname):
        """
        Generic json dump loader.
        """
        os.chdir(self.dumpdir)
        if '.' in dumpname:
            dumpname = dumpname.split('.')[0]
        with open(dumpname + '.json', 'r') as f:
            dumpdict = json.load(f)
        os.chdir(self.olddir)
        return dumpdict

        
class MasterGrabber(GPRMaster):
    """
    This is the master class for all grabbers. 
    """
    def __init__(self):
        super().__init__()
        
    
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
