"""
Runners should not move files explicitly.  All file movement
should be done by primers and then called in the runner.
"""
import shutil
import os

import numpy as np 
import fastppprimer
from master import MasterRunner


class FastppRunner(MasterRunner):
    """
    Contains methods to run FAST++.
    """
    def __init__(self, paramfile=None, oldfast=False):
        """ Init method for FastppRunner object.

        Args:
            paramfile (str): User can specify a .param file instead of
                assumed default self._fname.param.  Note that all other files
                used or created by FAST++ will use this name as well.
                Default is None.
            
            oldfast (bool): Use IDL FAST instead of FAST++.  Default is False.
        """

        super().__init__()

        # specify the correct program name:
        if oldfast:
            self.programname = 'fast'
        else:
            self.programname = 'fast++'
        
        # set paramfile attribute:
        if paramfile:
            self.paramfile = paramfile.split('.')[0]
        else:
            self.paramfile = self._fname
        
        # instantiate primer object as attribute:
        self.primer = fastppprimer.FastppPrimer()

        # load filename-objid dump:
        self.fo_dict = self._dumploader(self._fname_obj_jd)

    def runfastpp_sp(transfile=None, cmd=None, **kwargs):
        """ Runs FAST++ with spectra and photometry.

        Args:
            transfile (str): A specific source .translate can be used
                instead of the default.  Default is None.

            cmd (str or List[str]): User can specify a custum terminal
                that is used to run FAST++

            kwargs: Used to specify specific changes to be made to FAST++
                paramter settings.
        """

        # Organize spectra data FAST++:
        self.primer.spec_looper()

        # ftr : files to run:
        self.ftrlist = self.primer.filelist
        for f in self.ftrlist:

            # This will be the FAST++ file name:
            specdatafname = f.split('.')[1]
            fastfilename = specdatafname

            # Create param dictionary with changes:
            paramdict = self.primer._param_changer(
                kwargs, fastfilename, True, paramfile=self.paramfile 
            )

            # create files for FAST++:
            self._fastpp_filemaker(
                fastfilename, paramdict, 
                specdatafname=specdatafname, transfile=transfile
            )

            # clean up or create cmd:
            cmd = self._fastpp_cmd_cleaner(fastfilename, cmd=cmd)
            
            # Run FAST++:
            self.runner(cmd)

        # regroup the separate .fout files:
        fastppprimer.FastppFoutGrouper.regrouper()

        return True

    def runfastpp_p(transfile=None, cmd=None, **kwargs):
        """ Runs FAST++ with photometry only.

        Args:
            transfile (str): A specific source .translate can be used
                instead of the default.  Default is None.

            cmd (str or List[str]): User can specify a custum terminal
                that is used to run FAST++

            kwargs: Used to specify specific changes to be made to FAST++
                paramter settings.
        """
        # This will be the FAST++ file name:
        fastfilename = self._fname

        # Create param dictionary with changes:
        paramdict = self.primer._param_changer(
            kwargs, fastfilename, True, paramfile=self.paramfile 
        )

        # create files for FAST++:
        self._fastpp_filemaker(
            fastfilename, paramdict, 
            specdatafname=specdatafname, transfile=transfile
        )

        # clean up or create cmd:
        cmd = self._fastpp_cmd_cleaner(fastfilename, cmd=cmd)
        
        # Run FAST++:
        self.runner(cmd)

    def _fastpp_filemaker(
        self, fastfilename, paramdict, specdatafname=None, transfile=None
    ):
        """ Creates files needed to run FAST++.
        """

        # Default value for objid is None:
        objid = None

        # Create .spec file:
        if specdatafname:
            objid = self.fo_dict[specdatafname]
            specdatafname = transfile.split('.')[0]
            shutil.copyfile(specdatafname + '.specfile', fastfilename + '.translate')

        # Create .translate file:
        if transfile:
            transfile = transfile.split('.')[0]
            shutil.copyfile(transfile + '.translate', fastfilename + '.translate')
        else:
            shutil.copyfile(fastfile + '.translate', fastfilename + '.translate')

        # Create new .param file:
        with open(fastfilename + '.param', 'w+') as f:
            for key, value in paramdict.items():
                newline = key + ' = ' + value + '\n'
                f.write(newline)

        # Create .cat file:
        self.primer.cat_maker(objid=objid, catname=fastfilename)

    def _fastpp_cmd_cleaner(self, fastfilename, cmd=None):
        """ This method is used to clean up a user-provided FAST++ command.

        Args:
            fastfilename (str): File name that FAST++ will look for.

            cmd (str List[str]): Terminal command for running FAST++.  If it
                is a string, then the command will be converted to a list.  If
                cmd is None, then default FAST++ terminal command is used.
                Default is None.

        Returns:
            List[str]: Command for use by runner method, and thus 
                subprocess.Popen().
        """
        if not cmd:
            return [self.programname, fastfilename.split('.')[0] + '.param']

        elif type(cmd) == str:
            cmd = cmd.split(' ')
        
        # get rid of .param file in custom command:
        msk = ['.param' not in x for x in cmd]
        cmd = [cmd[i] for i in range(len(msk)) if msk[i]]

        return cmd
