import fastpprunner
import spectragrabber

sdssspecdatadir='specdata'
sdssroot = 'https://data.sdss.org/sas/dr12ß/'

grabber = spectragrabber.SdssSpectraGrabber(specdatadir=sdssspecdatadir)
grabber.sdss_spectra_grabber(url=sdssroot)

x = fastpprunner.FastppRunner()
x.runfastpp_sp(LIBRARY='bc03', RESOLUTION='hr', IMF='sa', SFH='exp')
