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

        # instantiate a regrouper object:
        self.regrouper = fastppprimer.FastppFoutGrouper()

        # load filename-objid dump:
        self.fo_dict = self._dumploader(self._fname_obj_jd)

    def runfastpp_sp(self, transfile=None, cmd=None, **kwargs):
        """ Runs FAST++ with spectra data and photometry data.

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

            # reset cmd variable:
            fcmd = cmd

            # This will be the FAST++ file name (spec data name + fname):
            fastfilename = self._fname + '-' + f.split('.')[0]
            specfilename = f
            
            # Create param dictionary with changes:
            paramdict = self.primer._param_changer(
                kwargs, fastfilename, True, paramfile=self.paramfile 
            )

            # create files for FAST++:
            self._fastpp_filemaker(
                fastfilename, paramdict, 
                specfilename, transfile=transfile
            )

            # clean up or create cmd:
            fcmd = self._fastpp_cmd_cleaner(fastfilename, cmd=fcmd)
                        
            # Run FAST++:
            self.runner(fcmd)

        # regroup the separate .fout files:
        self.regrouper.regrouper()

        return True

    def runfastpp_p(self, transfile=None, cmd=None, **kwargs):
        """ Runs FAST++ with photometry data only.

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
            kwargs, f, True, paramfile=self.paramfile 
        )

        # create files for FAST++:
        self._fastpp_filemaker(
            fastfilename, paramdict, 
            False, transfile=transfile
        )

        # clean up or create cmd:
        cmd = self._fastpp_cmd_cleaner(fastfilename, cmd=cmd)
        
        # Run FAST++:
        self.runner(cmd)

    def _fastpp_filemaker(
        self, fastfilename, paramdict, specdatafname=None, transfile=None
    ):
        """ Creates files needed to run FAST++.

        Args:
            fastfilename (str): This is thef file name that FAST++ will look
                for.

            paramdict (Dict[str]): This is a dictionary of FAST++ parameters and
                values that will be saved as a .param file with file name
                'fastfilename'.

            specdatafname (str): If given, then a .spec file will be created
                with name 'fastfilename'. Default is None.

            transfile (str): If provided, <transfile>.transfile will be copied
                to a new transfile <fastfilename>.transfile.  Default is None.

        Returns:
            bool: True if successful.
        """

        # Default value for objid is None:
        
        os.chdir(self._fdir)

        # Create .translate file:
        if transfile:
            transfile = transfile.split('.')[0]
            shutil.copyfile(transfile + '.translate', fastfilename + '.translate')

        # if no translate file is given, then use <self._fname>.translate:
        else:
            shutil.copyfile(self._fname + '.translate', fastfilename + '.translate')

        # Create new .param file:
        with open(fastfilename + '.param', 'w+') as f:
            for key, value in paramdict.items():
                newline = key + ' = ' + value + '\n'
                f.write(newline)
        
        os.chdir(self._olddir)

        # Create .cat file:
        self.primer.cat_maker(specdatafname=specdatafname)

        return True

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
        # msk = ['.param' not in x for x in cmd]
        # cmd = [cmd[i] for i in range(len(msk)) if msk[i]]

        return cmd
