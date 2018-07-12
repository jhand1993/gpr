import fastpprunner
import spectragrabber

sdssspecdatadir='specdata'
sdssroot = 'https://data.sdss.org/sas/dr12/'

grabber = spectragrabber.SdssSpectraGrabber(specdatadir=sdssspecdatadir, url=sdssroot)
grabber.sdss_spectra_grabber()

x = fastpprunner.FastppRunner()
x.fastpp_runner(includespec=True, LOG_TAU_MIN=7.0)
