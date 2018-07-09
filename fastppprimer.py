"""
spectra key and photo key will need to be specified...
can't just hardcode specObjID and objID.
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
    """
    Will likely rewrite this to be inherited from astropy.io.fits.Fits
    class, but this works for now.
    """
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        try:
            # Grab and set spectra data path from dump:
            specdatadir = self.dumploader(
                self.specdatadir_name_jdump
            )[self.specdatadir_name_jdump]
            specdatadir = pl.Path(self.fdir) / specdatadir
            os.chdir(specdatadir)

            # empty spectradata array for later use:
            self.spectradata = []

            # Grab the fits data (which is a list of tuples)
            # and store as a 2D array:
            self.fitsobj = fits.open(self.filename)
            list_of_tuples = list(self.fitsobj[1].data)
            self.fitsarr = np.array([list(x) for x in list_of_tuples])

            # converted to Angstroms
            self.wavelength = 10 ** (np.copy(self.fitsarr[:, 1]))
            self.flux = np.copy(self.fitsarr[:, 0])

            # converted to error from inverse variance
            self.fluxerr = 1 / np.sqrt(np.copy(self.fitsarr[:, 2])) 
            os.chdir(self.olddir)
        except Exception as e:
            raise


class FastppPrimer(MasterPrimer):
    """
    This class instantiates priming methods for a given input datafile
    containing the necessary columns to creat a .cat file. It can also
    create the .spec files from respective fits files if said files
    have already been grabbed.
    """
    def __init__(
        self, 
        binsize=10, 
        lambdastep=0.5, 
        lambdarange=(3800., 9000.)
    ):
        super().__init__()

        # create spectra data dictionary to grab spectra data directory:
        specdatadict = self.dumploader(self.specdatadir_name_jdump)
        self.specdatadir = self.fdir / str(
            specdatadict[self.specdatadir_name_jdump]
        )

        # create 'specdatadir' if it does not exist
        self.specdatadir.mkdir(exist_ok=True)

        # set keyword attributes:
        self.binsize = binsize
        self.lambdarange = lambdarange
        self.lambdastep = lambdastep

        # empty file list and spectra list for later use:
        self.filelist = []
        self.spectralist = []

        # create dump dictionaries:
        self.fs_dict = self.dumploader(self.fname_spec_jdump)
        self.fo_dict = self.dumploader(self.fname_obj_jdump)

    def spec_maker(self, spectra):
        """
        Makes a <filename>.spec for each fits file to use with FAST++ using
        refined spectra format:
        https://github.com/cschreib/fastpp#better-treatment-of-spectra
        ~1 Angstrom seems to be the spacing of spectra data from SDSS
        spectra fits.  Numpy was used as opposed to pandas due to the
        'double binning' required for FAST(++).
        """

        # create dump dictionaries.  Note these are only needed
        # if spectra is beig used:
        self.fs_dict = self.dumploader(self.fname_spec_jdump)
        self.fo_dict = self.dumploader(self.fname_obj_jdump)
        
        # set local variables
        binarr = []
        binsize = self.binsize
        lambdastep = self.lambdastep
        if self.lambdarange[1] - self.lambdarange[0] <= 0:
            print('Invalid wavelength range.')
            return False
        bincount = int(
            np.ceil(self.lambdarange[1] - self.lambdarange[0]) /
            (binsize * self.lambdastep)
            )
        for i in range(bincount):
            x = 0
            while x < self.binsize:
                binarr.append(i)
                x += 1

        # find the objID corresponding to 'filename':
        objID = self.fo_dict[str(spectra.filename)]

        # This is a format array for saving array to file:
        datafmt = [
            '%i', '%1.2f', '%1.2f', '%1.2f', '%1.2f'
            ]
        
        # This is the header for the .spec file:
        specheader = [
            'bin', 'wl_low', 'wl_high', 'F' + str(objID), 'E' + str(objID)
            ]
        
        # mega_arr is the array that will be saved to a .spec file:
        mega_arr = np.expand_dims(np.array(binarr, dtype=float), 0)
        rowcount = len(binarr)

        # create and append wl_low and wl_high columns:
        wlow = np.linspace(
            self.lambdarange[0], self.lambdarange[1], rowcount + 1
            )[:-1]
        whigh = np.linspace(
            self.lambdarange[0], self.lambdarange[1], rowcount + 1
            )[1:]
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
                j += 1
            
            # if the wavelength data is less than the
            # upper bound, add the data to current flux and
            # flux error value:
            while wl_data[j] < wl_highmax:
                cf_data.append(f_data[j])
                cferr_data.append(ferr_data[j])
                j += 1

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

        # only grab the filename from 'filename', not the filename + extension:
        fullname = self.fname + '-' + spectra.filename.split('.')[0]

        # note that the transpose of mega_arr is saved as file:
        np.savetxt(
            fullname + '.spec', mega_arr.T, 
            fmt=datafmt, delimiter='\t\t', header='\t\t'.join(specheader)
            )
        return fullname, objID

    def spec_looper(self):
        """
        Creates .spec files for each fits file in attribute 'self.filelist'.
        If True, 'jsondump' creates a .json file with objID as keys and full
        .spec file name as values.
        """
        self.json_fullname_obj = 'fullname-objID'
        if not self.spectralist:
            # probably isn't populated, but no need to rerun this if it is.
            self.filelist = list(self.dumploader(self.fname_obj_jdump).keys())

            # Instantiate all spectra data files listed in self.filelist.
            # this is the slowest part of the pipeline by far:
            self.spectralist = [SpectraData(f) for f in self.filelist]
        os.chdir(self.fdir)

        # these lists are used to create a data dump:
        f_fullnamelist = []
        f_objIDlist = []
        for f in self.spectralist:
            # Not sure why I used 'f' here, but whatever.
            f_fullname, f_objID = self.spec_maker(f)
            f_fullnamelist.append(f_fullname)
            f_objIDlist.append(f_objID)
        # make a dump for fullnames and object ID:
        self.dumpmaker(self.json_fullname_obj, f_fullnamelist, f_objIDlist)
        os.chdir(self.olddir)
        return f_fullnamelist

<<<<<<< HEAD
    def cat_maker(self, filename=None, includephot=True):
=======
    def cat_maker(self, filename=self.fname + '.csv', includephot=True):
>>>>>>> 0a3bbc6c2a14188a294fd37789610624f67c2685
        """
        This creates a catalog used by FAST++ for photometry. It makes
        heavy use of pandas dataframes 'filter' method to rename columns
        to include the required 'F_' and 'E_' prefixes for running FAST++.
        Miscelleneous columns are tacked at the end and are provided via
        keyword argument 'includecolumns', which can be a string or a list.
        Otherwise unnecessary columns will be deleted are deleted.
        """
        # If 'filename' is None, then use default filename for grabbed
        # data:
        if not filename:
            filename = self.fname + '.csv'
        
        os.chdir(self.fdir)

        # read grabbed data:
        df = pd.read_csv(filename, header=0, na_values='null')
        
        # this expression is used to grab the correct columns from df:
        filterexpression = r'\bobjID\b|\bspecObjID\b|\bz_spec\b|[E|F](_)[a-zA-Z]{1}'

        # filter out, rename, and break up df to be reorganized:
        df = df.filter(regex=filterexpression, axis=1)
        df = df.rename(columns={'objID': '#ID'})
        specObjID_df = df.loc[:, 'specObjID']
        df = df.drop('specObjID', axis=1)
        z_df = df.loc[:, 'z_spec']
        df = df.drop('z_spec', axis=1)

        # changes the NaN values to 0:
        for i in range(len(specObjID_df)):
            if np.isnan(specObjID_df[i]):
                specObjID_df[i] = 0.
        newdf = pd.concat([df, z_df, specObjID_df.astype(int)], axis=1)

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
        os.chdir(self.olddir)
        return True


class FastppFoutGrouper(MasterPrimer):
    """
    This is an odd class as it primes data after the application
    FAST++ has been ran. Nevertheless it is it's own primer as it is
    functionally separate from the other FAST++ primer class.
    """
    def __init__(self, foutdir):
        super().__init__()
        self.foutdir = self.fdir / foutdir

        # create 'foutdir' if it does not exist:
        self.foutdir.mkdir(exist_ok=True)

        # load fullname_obj dump:
        self.fno_dict = self.dumploader(self.fullname_obj_jdump)

    def regrouper(self):
        """
        Combines the individual .fout files for each galaxy into a composite
        .fout file.
        """
        os.chdir(self.foutdir)

        # grab all .fout files created by fast++:
        foutlist = glob.glob('*.fout')

        # get rid of .fout extension in string:
        foutlist = [x.split('.')[0] for x in foutlist]

        # rowlist will be appended with rows of data from .fout
        rowlist = []
        headerchecker = False
        header = ''
        for fout in foutlist:
            try:
                objID = self.fno_dict[fout]
            except KeyError:

                # if .fout file is not found in json dump, then it is
                # ignored:
                print(
                    fout + ' not found in ' + self.jsonname_fullname_objID +
                    '.json and will be ignored.'
                )
                objID = ''
                pass
            except:
                raise
            if not objID:
                pass
            with open(fout + '.fout', 'r') as f:
                while True:
                    row = f.readline()

                    # just in case some rows have a newline while others don't?
                    row = row.replace('\n', '')

                    # this specificies the fast++ header, and the beginning
                    # of data:
                    if '#                  id' in row and not headerchecker:
                        headerchecker = True
                        header = row

                    # append the row in .fout that corresponds to objID:
                    if objID in row:
                        rowlist.append(row)
                        f.close()
                        break
                    
                    # close file if at the end of file:
                    elif not row:
                        f.close()
                        break
        os.chdir(self.fdir)

        # create and write composite .fout file:
        compositefoutname = self.fname + '-composite'
        with open(compositefoutname + '.fout', 'w+') as f:
            f.write(header + '\n')
            for row in rowlist:
                f.write(row + '\n')
            f.close()
        os.chdir(self.olddir)
        return True
