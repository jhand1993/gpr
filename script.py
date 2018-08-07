import fastpprunner
import spectragrabber
import fastppplotter
import json

sdssspecdatadir='specdata'
sdssroot = 'https://data.sdss.org/sas/dr12/'
testid = '1237663543150837809'

grabber = spectragrabber.SdssSpectraGrabber(specdatadir=sdssspecdatadir)
grabber.sdss_spectra_grabber(url=sdssroot)

x = fastpprunner.FastppRunner()
x.runfastpp_sp(LIBRARY='bc03', RESOLUTION='hr', IMF='sa', SFH='exp', AUTO_SCALE='0')    

plots = fastppplotter.FastppSEDplotter()
objids = list(plots.fo_dict.values())
for ids in objids:
    plots.photospecplotter(ids, 'objID', 'sdss')