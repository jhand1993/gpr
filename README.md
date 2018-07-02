# GPR
"I'll do this tomorrow." - first version of the README

## Introduction
GPR stands for Grabbers, Primers, Runners.  This framework emphasizes modularization over efficiency, and is intended to enable addition of features without breaking any other part of the library.  There are other frameworks that incorporate these principles, and the main reason GPR exists is because the creator (aka me) had no idea what frameworks to look into. 

GPR specifically serves as a Python wrapper for the plethora of diverse (and divergent) command-line programs written by the Astronomy/Cosmology community while simplifying data-gathering for said programs.  As datasets from surveys grow, our reliance on more intricate data storage grows rapidly.  The idea here is to set in place a framework that can grow over time to simplify 
research workflow and decrease the amount of time used gathering, organizing, and preparing data for use with the myriad of programs used in research.

## Components
In principle, each application that is to 'wrapped' with GPR will contain a grabber class, primer class, and runner class.  As the childish naming convention subjects grabbers 'grab' data from some source, primers 'prime' grabbed data so to be used by some program, and runners 'run' said program.  The driving requirement of GPR is that there is to be no code interdependance between grabbers, primers, and runners.  Communication of data between grabbers, primers, and runners is done exclusively by JSON dumps called 'dumps' (because why not).

### Grabbers
Grabbers either upload local data, or communicate with some web server or database to grab the prerequisite data require by a program.  For example, if photometry is to be done with the aptly named [SExtractor](https://www.astromatic.net/software/sextractor) (Bertin, E. & Arnouts, S. 1996) via GPR, then the SExtractor grabber class will grab the required FITS files from their source, and said grabber class will be tailored to do so using the required techinques.

Because of APIs it is possible create unitize core grabbers instead of creating ones' own.  These core grabbers (which do not exist right now) will include a [CasJobs](https://skyserver.sdss.org/CasJobs/default.aspx) grabber, a [SkyQuery](http://voservices.net/skyquery/?token=) grabber, an [OACAPI](https://github.com/astrocatalogs/OACAPI) grabber, a wget-style grabber, and so on.  It is hoped that a faster FITS reader/writer than [astropy.io.fits](http://www.astropy.org/) (no offense) will be integrated in the future, but that is by no means a priority and will likely be really, really hard.

### Primers
Primers are going to be the most heterogeneous component to any GPR workflow, as each primer must be tailored for the program that is being wrapped.  Each program takes different input formats, but in principle these inputs are either parameters or tediously organized data structures (like tables or datacubes).  Primers can also be used on program output files.  Most importantly, primers cannot be used to run said program, nor to grab data to be primed.

Some programs that primers will be created for will hopefully include [FAST](http://w.astro.berkeley.edu/~mariska/FAST.html)([++](https://github.com/cschreib/fastpp)), [Starlight](http://adsabs.harvard.edu/abs/2011ascl.soft08006C), [SNANA](http://snana.uchicago.edu/), [AstrOmatic](https://www.astromatic.net/), [PEGASE](http://www2.iap.fr/pegase/), and hopefully others in the future. 

### Runners
Runners will make use of the subprocess package (and maybe multithreading?) to run the program desired to be run.  I have not thought enough about this part, so I am going to stop while I am ahead.
