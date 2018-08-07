import fastpprunner
import spectragrabber
import fastppplotter

sdssspecdatadir='specdata'
sdssroot = 'https://data.sdss.org/sas/dr12/'
testid = '1237663543150837809'

grabber = spectragrabber.SdssSpectraGrabber(specdatadir=sdssspecdatadir)
grabber.sdss_spectra_grabber(url=sdssroot)

x = fastpprunner.FastppRunner()
x.runfastpp_sp(LIBRARY='bc03', RESOLUTION='hr', IMF='sa', SFH='exp')    

plots = fastppplotter.FastppSEDplotter()
plots.photospecplotter(testid, 'objID', 'sdss')