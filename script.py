import fastpprunner
import spectragrabber

sdssspecdatadir='specdata'
sdssroot = 'https://data.sdss.org/sas/dr14'

# grabber = spectragrabber.SdssSpectraGrabber(specdatadir=sdssspecdatadir, url=sdssroot)
# grabber.sdss_spectra_grabber()

x = fastpprunner.FastppRunner()
x.fastpp_runner(includespec=False)