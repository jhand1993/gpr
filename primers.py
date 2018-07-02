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
            # sort of a nonstandard way of getting specdata path:
            specdatadir = self.dumploader(
                self.specdatadir_name_jdump
            )[self.specdatadir_name_jdump]
            specdatadir = pl.Path(self.fdir) / specdatadir
            os.chdir(specdatadir)
            self.spectradata = []
            self.fitsobj = fits.open(self.filename)
            list_of_tuples = list(self.fitsobj[1].data)
            self.fitsarr = np.array([list(x) for x in list_of_tuples])
            # converted to Angstroms
            self.wavelength = 10 ** (np.copy(self.fitsarr[:, 1]))
            self.flux = np.copy(self.fitsarr[:, 0])
            # converted to error from inverse variance
            self.fluxerr = 1 / np.sqrt(np.copy(self.fitsarr[:, 2])) 
            os.chdir(self.olddir)
        except:
            raise


class FastppPrimer(MasterPrimer):
    """
    This class instantiates priming methods for a given input datafile
    containing the necessary columns to creat a .cat file. It can also
    create the .spec files from respective fits files if said files
    have already been grabbed.
    """
    def __init__(
        self, binsize=10, 
        lambdastep=0.5, 
        lambdarange=(3800., 9000.)
    ):
        super().__init__()
        specdatadict = self.dumploader(self.specdatadir_name_jdump)
        self.specdatadir = self.fdir / str(
            specdatadict[self.specdatadir_name_jdump]
        )
        # create 'spedatadir' if it does not exist
        self.specdatadir.mkdir(exist_ok=True)

        self.binsize = binsize
        self.lambdarange = lambdarange
        self.lambdastep = lambdastep
        self.fname_spec_jdump = 'filename-specObjID'
        self.fname_obj_jdump = 'filename-objID'
        self.filelist = []
        self.spectralist = []
        try:
            self.fs_dict = self.dumploader(self.fname_spec_jdump)
            self.fo_dict = self.dumploader(self.fname_obj_jdump)
        except json.JSONDecodeError as e:
            print('JSON dumps from grabber we not uploaded.')
            print(str(e))
            self.fs_dict = {}
            self.fo_dict = {}
        except:
            raise

    def spec_maker(self, spectra):
        """
        Makes a <filename>.spec for each fits file to use with FAST++ using
        refined spectra format:
        https://github.com/cschreib/fastpp#better-treatment-of-spectra
        ~1 Angstrom seems to be the spacing of spectra data from SDSS
        spectra fits.  Numpy was used as opposed to pandas due to the
        'double binning' required for FAST(++).
        """
        binarr = []
        binsize = self.binsize
        lambdastep = self.lambdastep
        if self.lambdarange[1] - self.lambdarange[0] <= 0:
            print('Invalid wavelength range.')
            return False
        bincount = int(
            np.ceil(self.lambdarange[1] - self.lambdarange[0]) /
            (binsize * lambdastep)
            )
        for i in range(bincount):
            x = 0
            while x < binsize:
                binarr.append(i)
                x += 1
        if not self.fs_dict or not self.fo_dict:
            print('JSON dumps have not been uploaded.')
            return False
        elif not isinstance(spectra, SpectraData):
            print('Input \'fitsfile\' is not instance of \'SpectraData\'.')
            return False
        # find the objID corresponding to 'filename':
        objID = self.fo_dict[str(spectra.filename)]
        datafmt = [
            '%i', '%1.2f', '%1.2f', '%1.2f', '%1.2f'
            ]
        specheader = [
            'bin', 'wl_low', 'wl_high', 'F' + str(objID), 'E' + str(objID)
            ]
        mega_arr = np.expand_dims(np.array(binarr, dtype=float), 0)
        rowcount = len(binarr)
        wlow = np.linspace(
            self.lambdarange[0], self.lambdarange[1], rowcount + 1
            )[:-1]
        whigh = np.linspace(
            self.lambdarange[0], self.lambdarange[1], rowcount + 1
            )[1:]
        mega_arr = np.append(mega_arr, np.expand_dims(wlow, 0), axis=0)
        mega_arr = np.append(mega_arr, np.expand_dims(whigh, 0), axis=0)
        wl_data = np.copy(spectra.wavelength)
        f_data = np.copy(spectra.flux)
        ferr_data = np.copy(spectra.fluxerr)
        flux_arr = np.zeros(rowcount)
        fluxerr_arr = np.zeros(rowcount)
        j = 0
        for k in range(bincount):
            cf_data = []
            cferr_data = []
            wl_lowmin = wlow[k*binsize]
            # wl_lowmax = wlow[k*binsize + binsize - 1]
            # wl_highmin = whigh[k*binsize]
            wl_highmax = whigh[k*binsize + binsize - 1]
            while wl_data[j] < wl_lowmin:
                j += 1
            while wl_data[j] < wl_highmax:
                cf_data.append(f_data[j])
                cferr_data.append(ferr_data[j])
                j += 1
            f_mean = np.mean(cf_data)
            ferr_sum = np.sqrt(np.sum([x**2 for x in cferr_data]))
            if binsize == 1:
                flux_arr[k] = f_mean
                fluxerr_arr[k] = ferr_sum
            else:        
                flux_arr[k*binsize:k*binsize + binsize] = f_mean
                fluxerr_arr[k*binsize:k*binsize + binsize] = ferr_sum
        mega_arr = np.append(mega_arr, np.expand_dims(flux_arr, 0), axis=0)
        mega_arr = np.append(mega_arr, np.expand_dims(fluxerr_arr, 0), axis=0)
        mega_arr[1:, :][mega_arr[1:, :] == 0.] = np.nan
        # only grab the filename from 'filename', not the filename + extension:
        fullname = self.fname + '-' + spectra.filename.split('.')[0]
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
            # this is the slowest part of the pipeline by far:
            self.spectralist = [SpectraData(f) for f in self.filelist]
        os.chdir(self.fdir)
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

    def cat_maker(self, ignorphot=False):
        """
        This creates a catalog used by FAST++ for photometry. It makes
        heavy use of pandas dataframes 'filter' method to rename columns
        to include the required 'F_' and 'E_' prefixes for running FAST++.
        """
        os.chdir(self.fdir)

        def nm_to_mj(x):
            # converts nanomaggies to microjanksys.
            return x * 3.631
        df = pd.read_csv(self.fname + '.csv', header=0)
       
        # Break up the dataframe into different components 
        # to be reorganized
        err_df = df.filter(like='E_', axis=1)
        id_df = df.filter(items=['objID'], axis=1)
        flux_df = df.filter(like='F_', axis=1)
        z_df = df.filter(like='z_', axis=1)
        specid_df = df.filter(items=['specObjID'], axis=1)
        id_df = id_df.rename(columns={'objID': '#ID'})

        err_df.loc[:, :] = 1 / np.sqrt(err_df.loc[:, :])
        err_df.loc[:, :] = nm_to_mj(err_df.loc[:, :])
        flux_df.loc[:, :] = nm_to_mj(flux_df.loc[:, :])

        if not ignorphot:
            df = pd.concat([id_df, specid_df, flux_df, err_df, z_df], axis=1)
        else:
            df = pd.concat([id_df, z_df], axis=1)

        # Save the dataframe as a .csv.
        df.to_csv(self.fname + '.cat', sep='\t', index=False)
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

        self.jsonname_fullname_objID = 'fullname-objID'
        try:
            os.chdir(self.dumpdir)
            print(os.getcwd())
            with open(self.jsonname_fullname_objID + '.json', 'r') as f:
                self.fno_dict = json.load(f)
                f.close()
            os.chdir(self.olddir)
        except json.JSONDecodeError as e:
            print('JSON dumps from grabber we not uploaded.')
            print(e)
            self.fno_dict = {}


    def regrouper(self):
        """
        Combines the individual .fout files for each galaxy into a composite
        .fout file.
        """
        os.chdir(self.foutdir)
        foutlist = glob.glob('*.fout')
        # get rid of .fout extension in string:
        foutlist = [x.split('.')[0] for x in foutlist]
        rowlist = []
        headerchecker = False
        header = ''
        for fout in foutlist:
            try:
                objID = self.fno_dict[fout]
            except KeyError:
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
                    if '#                  id' in row and not headerchecker:
                        headerchecker = True
                        header = row
                    if objID in row:
                        rowlist.append(row)
                        f.close()
                        break
                    elif not row:
                        f.close()
                        break
        os.chdir(self.fdir)
        compositefoutname = self.fname + '-composite'
        # create and write composite .fout file:
        with open(compositefoutname + '.fout', 'w+') as f:
            f.write(header + '\n')
            for row in rowlist:
                f.write(row + '\n')
            f.close()
        os.chdir(self.olddir)
        return True
