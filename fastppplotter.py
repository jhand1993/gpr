import matplotlib.pyplot as plt
import numpy as np
import astropy.io.fits as fits
from astropy import constants as const
import pandas as pd
import os
import glob
from master import GPRMaster


class FastppSEDplotter(GPRMaster):
    """ Contains methods for plotting and comparing FAST++ fits.
    """

    def __init__(self):
        """ Initializer for class.
        """

        super().__init__()

        # load spectra file name: objid pairs:
        self.fo_dict = self._dumploader(self._fname_obj_jd)

        # load spectra data directory:
        specdirname = self._dumploader(self._specdatadir_jd)['specdatadir-name']
        self._specdir = self._fdir / specdirname

    def photospecplotter(
        self, objid, objidcol, survey, 
        photodata_ext='csv', bestfitdir='best_fits', convert_to_ergs=True
    ):
        """ Method for plotting photometric data versus FAST++ best fit.

        Args:
            objid (str or int): Object identifier used to identify object.

            objidcol (str): Column name in photometry data file of object
                identifier.
            
            survey (str): Survey from which to grab pass band wavelengths in
                angstroms.  Wavelengths are stored in masterconfig.json.

            photodata_ext (str): File extension of the file from which
                photometry data is loaded from.  Default is '.csv'.

            bestfitdir (str): Directory to look for best fit SED from FAST++.
                Default is 'best_fits'.

            convert_to_ergs (bool): If True, then flux data will be converted
                to ergs.  Default is True.

        Return:
            bool: True if successful.
        """

        # load spectra data:
        spectra = self._specloader(objid=objid)

        # load photometry data:
        photometry = self._photoloader(objid=objid, objidcol=objidcol)

        # Convert photometry points to flux
        wlphotometry = self._fluxconverter(survey=survey)

        # Load the best fit data:
        bestfit = self._bestfitloader(objid=objid, bestfitdir=bestfitdir)

        plt.errorbar(wlphotometry)
        plt.errorbar(spectra[:, 0], spectra[:, 1], yerr=spectra[:, 2], 
            ecolor='red', color='red', fmt='-', label='Spectra'
        )
        plt.plot()


    def _specloader(self, objid):
        """ Internal method for loading spectra data.
        
        Args:
            objid (str or int): Object identifier used to identify object.

        Returns:
            np.array: Spectra data is returned as a numpy array.
        """
        os.chdir(self._specdir)

        # Invert keys and values:
        of_dict = self._dumpinverter(self.fo_dict)

        # Grab spec file:
        specfile = of_dict[str(objid)] + '.' + self._specext

        # Open fits data file:
        fitsobj = fits.open(specfile)

        # Convert tuples of data into an array:
        list_of_tuples = list(fitsobj[1].data)
        fitsarr = np.array([list(x) for x in list_of_tuples])

        # converted to Angstroms
        wavelength = 10 ** (np.copy(fitsarr[:, 1]))
        flux = np.copy(fitsarr[:, 0])

        # converted to error from inverse variance
        fluxerr = 1 / np.sqrt(np.copy(fitsarr[:, 2]))

        os.chdir(self._olddir) 

        return np.concatenate((wavelength, flux, fluxerr), axis=1)

    def _photoloader(self, objid, objidcol, photodata_ext):
        """ Internal method for loading photometry data for object.

        Args:
            objid (str or int): Object identifier.

            objidcol (str): Column name in photometry data file of object
                identifier.

            photodata_ext (str): File extension of the file from which
                photometry data is loaded from.

        Returns:
            array: Returns numpy array of photometry data.
        """
        os.chdir(self._fdir)

        cols = [1, 13, 14, 15, 16, 17]

        # Load photometry data:
        df = pd.read_csv(self._fname + '.csv', dtype=str, usecols=cols)

        # Find object in photometry data:
        is_objid = df[objidcol] == str(objid)
        objdf = df[is_objid]
        objdf = objdf.loc[:, 1:]
        print(objdf.values)

        os.chdir(self._olddir)
        return np.array(objdf.values)

    def _bestfitloader(self, objid, bestfitdir):
        """ Internal method used to load best fit data.

        Args:
            objid (str or float):  Object identifier.

            bestfitdir (str): Directory to look for best fit SED from FAST++.

        Returns:
            array (float): 2D array of wavelength and flux per unit wavelength.
        """

        # Change to best fit directory:
        os.chdir(self._fdir / bestfitdir)

        # Grab best fit files:
        fitfiles = glob.glob('*.fit')

        # Find the fit file corresponding to object of interest.
        fitfile = [str(objid) in x for x in fitfiles]

        return np.loadtxt(fitfile, dtype=float)

    def _fluxconverter(self, fluxdata, survey, convert_to_ergs=True):
        """ Internal method used to convert flux to wavelength.

        Args:
            fluxdata (iterable): Flux data that is to be converted to
                corresponding wavelength data.
            
            survey (str): Survey from which to grab pass band wavelengths in
                angstroms.  Wavelengths are stored in masterconfig.json.
            
            convert_to_ergs (bool): If True, then flux data will be converted
                to ergs.  Default is True.
        
        Returns:
            array(float): 2D array of wavelength andflux data in terms of
                unit flux.
        """

        # convert flux data to an array if it is not already one:
        if not isinstance(fluxdata, np.array):
            fluxarr = np.asarray(fluxdata)

        else:
            fluxarr = fluxdata
        
        # used in unit conversion:
        conversion_factor = 1.

        # Convert to ergs if necessary:
        if convert_to_ergs:
            
            # have to treat sdss special:
            if survey == 'sdss':
                conversion_factor = 3.631

            newfluxarr = fluxarr * 1e19 * conversion_factor * const.c.value

        bands = np.array(self._masterconfig['bands'][survey], type=float)

        return newfluxarr / (bands**2)

            

            



        







    

