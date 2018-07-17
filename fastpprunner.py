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

    """
    def fastpp_runner(
        self, includephot=True, includespec=True, cmd=None, **kwargs
    ):
         Runs FAST++

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
        
        # This is the default FAST++ command:
        if not cmd:
            cmd = [self.programname, self._fname + '.param']

        # if string is given as 'cmd', split it into a list:
        elif cmd and type(cmd) == str:
            cmd = cmd.split(' ')

        # if spectra are included, then loop through each object:
        if includespec:


                # Remove file extension and create new file name:
                fullname = self.paramfile + '-' + f.split('.')[0]

                # grab the objid from the filename:
                objid = fo_dict[f]

                self._param_changer(fullname, kwargs, includespec=True)
                
                # Make .cat file:
                self.primer.cat_maker(
                    objid=objid, catname=fullname, includephot=includephot
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

        else:
            # modify the parameters for .param file.
            self._param_changer(self.paramfile, kwargs, includespec=False)
            
            # make new .cat file:
            self.primer.cat_maker(includephot=includephot)
            self.runner(cmd)
            return True
    """
    def fastpp_sp(transfile=None):
        """ Runs FAST++ with spectra and photometry.
        """

        # Organize spectra data FAST++:
        self.primer.spec_looper()

        # ftr : files to run:
        self.ftrlist = self.primer.filelist
        for f in self.ftrlist:


    def _fastpp_filemaker(self, fastfile, paramdict, specfile=None, transfile=None):
        """ Creates files needed to run FAST++.
        """

        # Default value for objid is None:
        objid = None

        # Create .spec file:
        if specfile:
            objid = self.fo_dict[specfile]
            specfile = transfile.split('.')[0]
            shutil.copyfile(specfile + '.specfile', fastfile + '.translate')

        # Create .translate file:
        if transfile:
            transfile = transfile.split('.')[0]
            shutil.copyfile(transfile + '.translate', fastfile + '.translate')
        else:
            shutil.copyfile(fastfile + '.translate', fastfile + '.translate')

        # Create new .param file:
        with open(fastfile + '.param', 'w+') as f:
            for key, value in paramdict.items():
                newline = key + ' = ' + value + '\n'
                f.write(newline)

        # Create .cat file:
        self.primer.cat_maker(objid=objid, catname=fastfile)
        

