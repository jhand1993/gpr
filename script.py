import fastpprunner
import spectragrabber

sdssspecdatadir='specdata'
sdssroot = 'https://data.sdss.org/sas/dr14/'

grabber = spectragrabber.SdssSpectraGrabber(specdatadir=sdssspecdatadir)
grabber.sdss_spectra_grabber(url=sdssroot, include_photoid=False)

#x = fastpprunner.FastppRunner()
#x.fastpp_runner(includespec=True, LIBRARY='bc03', RESOLUTION='hr', IMF='sa', SFH='exp')
