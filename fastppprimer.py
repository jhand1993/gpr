"""
spectra key and photo key will need to be specified...
can't just hardcode specobjid and objid.
"""
import re
import os
import glob
import json
import pathlib as pl

import numpy as np
import pandas as pd
import astropy.io.fits as fits
from master import MasterPrimer


class SpectraData(MasterPrimer):
    """ Serves as a spectra object.

    """
    def __init__(self, filename):
        """ Creates instance of spectra file 'filename'.

        Args:
            filename (str): name of the spectra data file to be loaded
                into instantiated object.
        """
        super().__init__()
        self.filename = filename
        try:
            # Grab and set spectra data path from dump:
            specdatadir = self._dumploader(
                self._specdatadir_jd
            )[self._specdatadir_jd]
            specdatadir = pl.Path(self._fdir) / specdatadir
            os.chdir(specdatadir)

            # empty spectradata array for later use:
            self.spectradata = []

            # Grab the fits data (which is a list of tuples)
            # and store as a 2D array:
            print('Loading', filename, '...')
            self.fitsobj = fits.open(self.filename)
            list_of_tuples = list(self.fitsobj[1].data)
            self.fitsarr = np.array([list(x) for x in list_of_tuples])

            # converted to Angstroms
            self.wavelength = 10 ** (np.copy(self.fitsarr[:, 1]))
            self.flux = np.copy(self.fitsarr[:, 0])

            # converted to error from inverse variance
            self.fluxerr = 1 / np.sqrt(np.copy(self.fitsarr[:, 2])) 
            os.chdir(self._olddir)
        except Exception as e:
            raise


class FastppPrimer(MasterPrimer):
    """ Contains methods to prime data for use in FAST++

    """
    def __init__(self):
        """ Creates a priming object for FAST++.        
        """
        super().__init__()

        # load spectra data dictionary and grab spectra data directory:
        specdatadict = self._dumploader(self._specdatadir_jd)
        self._specdatadir = self._fdir / str(
            specdatadict[self._specdatadir_jd]
        )

        # empty file list and spectra list for later use:
        self.filelist = []
        self.spectralist = []

    def spec_maker(
        self, spectra, 
        customfullname=None, 
        binsize=10, lambdastep=0.5, lambdarange=(3800., 9000.)
    ):
        """ Makes a .spec for the spectra object refined FAST++ format.

        Attributes:
            spectra (Spectra[obj]): Must be an instance of Spectra class.
                Attributes of this class are used to create an array
                that bins flux/flux error data into correct wavelength
                intervals.

            customfullname (str): You can specify a custom addon to the
                fullname that is returned by the function.  Default is
                None.

            binsize (int): This is the size bin in the .spec file used by
                FAST++.  Default is 10.

            lambdastep (float): This is the size of the wavelength interval
                (in angstroms) of rows in the .spec file.  Default is 0.5.

            lambdarange (tuple[float]): this tuple represents the entire
                wavelength range spanned in the .spec file. Must have two 
                elements.  Default is (3800., 9000.).    

        Returns:
            fullname (str): This is the created file's name.  It combines
                the original spectra data file name with the file name 
                specified in the master configuration file.
            
            objid (str): This is the identifier relating the spectra file
                to corresponding photometric data.
        """

        # create dump dictionaries.  Note these are only needed
        # if spectra is being used:
        self.fs_dict = self._dumploader(self._fname_spec_jd)
        self.fo_dict = self._dumploader(self._fname_obj_jd)
        
        os.chdir(self._fdir)

        binarr = []

        # check to make sure the wavelength range given is valid:
        if lambdarange[1] - lambdarange[0] <= 0:
            print('Invalid wavelength range.')
            return False

        # calculate the total number of bins required:
        bincount = int(
            np.ceil(lambdarange[1] - lambdarange[0]) /
            (binsize * lambdastep)
            )

        # make the bin array with size equal to the total number
        # of rows ie 
        for i in range(bincount):
            x = 0
            while x < binsize:
                binarr.append(i)
                x += 1

        # find the objid corresponding to 'filename':
        objid = self.fo_dict[str(spectra.filename)]

        # This is a format array for saving array to file:
        datafmt = ['%i', '%1.2f', '%1.2f', '%1.2f', '%1.2f']
        
        # This is the header for the .spec file:
        specheader = [
            'bin', 'wl_low', 'wl_up', 'F' + str(objid), 'E' + str(objid)
            ]
        
        # mega_arr is the array that will be saved to a .spec file:
        mega_arr = np.expand_dims(np.array(binarr, dtype=float), 0)
        rowcount = len(binarr)

        # create and append wl_low and wl_high columns:
        wlow = np.linspace(lambdarange[0], lambdarange[1], rowcount + 1)[:-1]

        whigh = np.linspace(lambdarange[0], lambdarange[1], rowcount + 1)[1:]
        mega_arr = np.append(mega_arr, np.expand_dims(wlow, 0), axis=0)
        mega_arr = np.append(mega_arr, np.expand_dims(whigh, 0), axis=0)

        # grab relevant data from spectra files:
        wl_data = np.copy(spectra.wavelength)
        f_data = np.copy(spectra.flux)
        ferr_data = np.copy(spectra.fluxerr)
        flux_arr = np.zeros(rowcount)
        fluxerr_arr = np.zeros(rowcount)

        # This is a counter used apart from the for-loop count:
        j = 0
        for k in range(bincount):
            
            # 'c' in front of a variable name implies 'current':
            cf_data = []
            cferr_data = []

            # set the lower wavelength bound:
            wl_lowmin = wlow[k*binsize]

            # set the upper wavelength bound:
            wl_highmax = whigh[k*binsize + binsize - 1]

            # skip data from spectra information until
            # until data wavelength is at least equal
            # to the minimum wavelength bin:
            while wl_data[j] < wl_lowmin:

                # We don't want j to index past the length of the
                # wavelength data array 'wl_data':
                if j + 1 == len(wl_data):
                    break
                
                # otherwise continue as planned:
                else:
                    j += 1
            
            # if the wavelength data is less than the
            # upper bound, add the data to current flux and
            # flux error value:
            while wl_data[j] < wl_highmax:
                cf_data.append(f_data[j])
                cferr_data.append(ferr_data[j])

                # We don't want j to index past the length of the
                # wavelength data array 'wl_data':
                if j + 1 == len(wl_data):
                    break
                
                # otherwise continue as planned:
                else:
                    j += 1

            # if no data values exist in the bin, set
            # f_mean and ferr_sum to 'NaN':
            if len(cf_data) == 0:
                f_mean = 'NaN'
                ferr_sum = 'NaN'

            else:
                # calculate the mean value of fluxes in between
                # upper and lower wavelength bounds:
                f_mean = np.mean(cf_data)

                # similarly, calculate total error:
                ferr_sum = np.sqrt(np.sum([x**2 for x in cferr_data]))

            # set all rows in current bin to the average flux
            # and total error:
            if binsize == 1:
                flux_arr[k] = f_mean
                fluxerr_arr[k] = ferr_sum
            else:        
                flux_arr[k*binsize:k*binsize + binsize] = f_mean
                fluxerr_arr[k*binsize:k*binsize + binsize] = ferr_sum

        # append the flux and flux error arrays to mega_arr as new columns
        mega_arr = np.append(mega_arr, np.expand_dims(flux_arr, 0), axis=0)
        mega_arr = np.append(mega_arr, np.expand_dims(fluxerr_arr, 0), axis=0)

        # if any of the remaining values equal 0, set to NaN:
        mega_arr[1:, :][mega_arr[1:, :] == 0.] = np.nan

        # only grab the filename from 'filename', not the filename + extension.
        # If customfullname is given, then use that as the added string to the
        # .spec file.
        if customfullname:
            fullname = customfullname + '-' + spectra.filename.split('.')[0]
        
        else:
            fullname = self._fname + '-' + spectra.filename.split('.')[0]

        # note that the transpose of mega_arr is saved as file:
        np.savetxt(
            fullname + '.spec', mega_arr.T, 
            fmt=datafmt, delimiter='\t\t', header='\t\t'.join(specheader)
            )

        os.chdir(self._olddir)
        return fullname, objid

    def spec_looper(self):
        """ Creates .spec files for each fits file in attribute 'self.filelist'.

        Returns:
            f_fullnamelist (List[str]): This list contains all the full names of
                the .spec files for each spectra file in the spectra file data
                directory.
        """
        if not self.spectralist:

            # Grab all the spectra file names in a list from dump:
            try:
                self.filelist = list(
                    self._dumploader(self._fname_obj_jd).keys()
                )

                # Instantiate all spectra data files listed in self.filelist.
                # This is the slowest part of the pipeline by far:
                self.spectralist = [SpectraData(f) for f in self.filelist]
            
            # raise an error if dumps do not exist:
            except AttributeError as e:
                message = 'Make sure dumps have been created for spectra files.' 
                raise e(message)

            except Exception as e:
                raise
            
        os.chdir(self._fdir)

        # these lists are used to create a data dump:
        f_fullnamelist = []
        f_objidlist = []
        for f in self.spectralist:

            # Not sure why I used 'f' here, but whatever.
            f_fullname, f_objid = self.spec_maker(f)
            f_fullnamelist.append(f_fullname)
            f_objidlist.append(f_objid)

        # make a dump for fullnames and object ID:
        self._dumpmaker(self._fullname_obj_jd, f_fullnamelist, f_objidlist)

        os.chdir(self._olddir)
        return f_fullnamelist

    def cat_maker(self, filename=None, includephot=True):
        """ This creates a .cat file used by FAST++ for photometry.

        Args:
            filename (str): If specified, this is used as the photometric
                data file to create a .cat file from.  Default is None.

            includephot (bool): If true, .cat file will include photometric
                information.  Otherwise, only redshift will be included.
                Default is True.
        """

        # If 'filename' is None, then use default filename for grabbed
        # data:
        if not filename:
            filename = self._fname + '.csv'
        
        os.chdir(self._fdir)

        # create dataframe fom input file:
        df = pd.read_csv(filename, header=0, na_values='null')
        
        # this expression is used to grab the correct columns from df:
        filterexpression = r'\bobjID\b|\bspecObjID\b|\bz_spec\b|[E|F](_)[a-zA-Z]{1}'

        # filter out, rename, and break up dataframe to be reorganized:
        df = df.filter(regex=filterexpression, axis=1)
        df = df.rename(columns={'objID': '#ID'})
        specobjid_df = df.loc[:, 'specObjID']
        df = df.drop('specObjID', axis=1)
        z_df = df.loc[:, 'z_spec']
        df = df.drop('z_spec', axis=1)

        # changes the NaN values to 0:
        for i in range(len(specobjid_df)):
            if np.isnan(specobjid_df[i]):
                specobjid_df[i] = 0.
        newdf = pd.concat([df, z_df, specobjid_df.astype(int)], axis=1)

        # for each column, check to ee if values need to be changed:
        for col in list(newdf.columns):

            # This regex '[E](_)[a-zA-Z]' finds all E_* columns 
            # (flux error)
            if re.match(r'[E](_)[a-zA-Z]', col):
                newdf[col] = [self.nm_to_mj(1/np.sqrt(x)) for x in newdf[col]]
                newdf[col] = newdf[col].round(decimals=3)

            # This regex '[E](_)[a-zA-Z]' finds all F_* columns 
            # (flux)
            elif re.match(r'[E](_)[a-zA-Z]', col):
                newdf[col] = [self.nm_to_mj(x) for x in newdf[col]]
                newdf[col] = newdf[col].round(decimals=3)

        # Save the dataframe as a .csv.
        newfilename = filename.split('.')[0] + '.cat'
        newdf.to_csv(newfilename, sep='\t', index=False)
        print(newfilename + ' saved in ' + str(self._fdir) + '.')

        os.chdir(self._olddir)
        return True


class FastppFoutGrouper(MasterPrimer):
    """ This contains method to group .fout files into one composite file.
    """
    def __init__(self, foutdir):
        super().__init__()
        """ Initializes instance of FastppFoutGrouper class.
        """

    def regrouper(self):
        """
        Combines the individual .fout files for each galaxy into a composite
        .fout file.

        Returns:
            bool: True if successful.
        """

        # load fullname_obj dump.  Raise error if dump does not exist:
        try:
            self.fno_dict = self._dumploader(self._fullname_obj_jd)
        
        except Exception as e:
            message = 'Have you created .spec files for spectra data?'
            raise e(message)

        # grab all .fout files created by fast++:
        os.chdir(self._fdir)
        foutlist = glob.glob('*.fout')
        os.chdir(self._olddir)

        # get rid of .fout extension in string:
        foutlist = [x.split('.')[0] for x in foutlist]

        # rowlist will be appended with rows of data from .fout
        rowlist = []
        headerchecker = False
        header = ''
        
        # loop through .fout files:
        os.chdir(self._fdir)
        for fout in foutlist:
            try:
                # grab the objid from file name:
                objid = self.fno_dict[fout]

                with open(fout + '.fout', 'r') as f:
                    while True:
                        row = f.readline()

                        # just in case some rows have a newline while 
                        # others don't?
                        row = row.replace('\n', '')

                        # this specifies the FAST++ header and the 
                        # beginning of data:
                        colnamestart = '#                  id'
                        if colnamestart in row and not headerchecker:
                            headerchecker = True
                            header = row

                        # append the row in .fout that corresponds to 
                        # objid:
                        if objid in row:
                            rowlist.append(row)
                            break
                        
                        # close file if at the end of file:
                        elif not row:
                            break

            # if .fout file is not found in json dump, then it is
            # ignored:
            except KeyError:
                print(
                    fout + ' not found in ' + self._fullname_obj_jd +
                    '.json and will be ignored.'
                )
                pass
            except Exception as e:
                raise

        # create and write composite .fout file:
        compositefoutname = self._fname + '-composite'
        with open(compositefoutname + '.fout', 'w+') as f:
            f.write(header + '\n')

            # loop through all objects and append rows:
            for row in rowlist:
                f.write(row + '\n')

        os.chdir(self._olddir)
        return True
