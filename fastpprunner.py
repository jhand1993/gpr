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
            elf.programname = 'fast'
        else:
            self.programname = 'fast++'
        
        # set paramfile attribute:
        if paramfile:
            self.paramfile = paramfile.split('.')[0]
        else:
            self.paramfile = self._fname
        
        # instantiate primer object as attribute:
        self.primer = fastppprimer.FastppPrimer()
        
    def fastpp_runner(
        self, includephot=True, includespec=True, cmd=None, **kwargs
    ):
        """ Runs FAST++

        Args:
            includephot (bool): If true, then photometry will be included when
                running FAST++.  Default is True.

            includespec (bool): If true, then spectra data will be included when
                running FAST++.  FAST++ will be ran on each object with spectra
                individually and will ignore other objects.  Results of the
                individual runs are then recombined.  Default is True.

            cmd (str or List[str]): User can provide a custom terminal command
                to run FAST++.  If cmd is a string, then it will be split into
                a list of strings.  If cmd is None, then the command will be
                'fast++ <paramfile>.param.  Default is None.

            kwargs: User can specify other parameters to change in the in the
                FAST++ .param file.

            Returns:
                bool: True if successful.        
        """
        # This is the default FAST++ command:
        if not cmd:
            cmd = [self.programname, self._fname + '.param']

        # if string is given as 'cmd', split it into a list:
        elif cmd and type(cmd) == str:
            cmd = cmd.split(' ')

        # if spectra are included, then loop through each object:
        if includespec:
            try:
                # prime data for FAST++:
                self.primer.spec_looper()
                self.primer.cat_maker(includephot=includephot)

                # ftr : files to run:
                self.ftrlist = self.primer.filelist
                for f in self.ftrlist:

                    # Remove file extension and create new file name:
                    fullname = self.paramfile + '-' + f.split('.')[0]

                    self._param_changer(fullname, kwargs, includespec=True)
                    
                    # copy the .cat file with new file name:
                    os.chdir(self._fdir)
                    newcat = shutil.copyfile(
                        self.paramfile + '.cat', 
                        fullname + '.cat'
                    )

                    # copy the .translate file with new file name:
                    newtranslate = shutil.copyfile(
                        self.paramfile + '.translate', 
                        fullname + '.translate'
                    )

                    # change self.cmd for each file fullname:
                    cmd = [self.programname, fullname + '.param']
                    self.runner(cmd)

                # recombine each fast++ run on individual spectra into
                # new .fout file:
                grouper = fastppprimer.FastppFoutGrouper(foutdir='fout')
                grouper.regrouper()
                
                os.chdir(self._olddir)
                return True
            except Exception as e:
                raise
        else:
            try:
                self._param_changer(self.paramfile, kwargs, includespec=False)
                
                # make new .cat file:
                self.primer.cat_maker(includephot=includephot)
                self.runner(cmd)
                return True

            except Exception as e:
                raise

    def _param_changer(self, filename, paramchanges, includespec=True):
        """ Internal method used to create FAST++ .param file with necessary
            and provided changes.

        Args:
            filename (str): The catalog name in 'paramdict' will be changed 
                to the value of this filename.

            paramchanges (Dict[str]): This dict is generated from kwargs
                given by the user for other .param paramters to change.

            includespec (bool): Sets the .spec file name parameter in .param
                file.  Default is True.

        Returns:
            bool: True if successful.
        """

        # load .param data used by FAST++:
        os.chdir(self._fdir)

        # load .param data used by FAST++:
        paramdata = np.loadtxt(filename + '.param', dtype=str) 

        # grab .paramdata parameter:value pairs in dictionary:
        paramdict = dict(zip(paramdata[:, 0], paramdata[:, 2]))
    
        try:

            # Make changes to .param file specified by kwargs
            if paramchanges:
                for key, value in paramchanges.items():
                    paramdict[key] = value

            # 'CATALOG' argument always needs to be changed:
            paramdict['CATALOG'] = self.paramfile

            # Set correct spectra file name and settings.  Note that
            # .spec file extension is not included:
            if includespec:
                paramdict['SPECTRUM'] = filename.split('.')[0]
                paramdict['AUTO_SCALE'] = '0'
                paramdict['APPLY_VDISP'] = '0'
            
            # change all .param values in new .param files specified
            # in kwargs:
            with open(filename + '.param', 'w+') as f:
                for key, value in paramdict.items():
                    newline = key + ' = ' + value + '\n'
                    f.write(newline)
            
            os.chdir(self._olddir)
            return True
        
        except Exception as e:
            raise

            

