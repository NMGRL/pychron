Pychron
========
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3237834.svg)](https://doi.org/10.5281/zenodo.3237834)
[![Format code](https://github.com/NMGRL/pychron/actions/workflows/format_code.yml/badge.svg)](https://github.com/NMGRL/pychron/actions/workflows/format_code.yml)
[![Pychron Install via EDM with unittest suite](https://github.com/PychronLabsLLC/pychron/actions/workflows/unittests.yml/badge.svg)](https://github.com/PychronLabsLLC/pychron/actions/workflows/unittests.yml)

[Changes](CHANGELOG.md)

[Website](http://nmgrl.github.io/pychron/)

[Documentation](http://pychron.readthedocs.org)

[Installation](https://github.com/NMGRL/pychron/wiki/Install)

[RoadMap](ROADMAP.md)

What is Pychron
===============

Pychron is a set of applications for the collection and processing of noble gas mass spectrometry data. Pychron is 
developed at the New Mexico Geochronology Research Laboratory at New Mexico Tech. Components of pychron are used 
within multiple research domains, but mainly for Ar-Ar geochronology and thermochronology. Pychron's main 
applications are pyValve, pyLaser, pyExperiment and pyCrunch. Additional components include RemoteControlServer.cs and 
Bakedpy.

Pychron aims to augment and replace the current widely used program Mass Spec by Alan Deino of Berkeley Geochronology Center

Give it a try
====================
Interested in seeing pychron in action? Don't want to/can't install all the required dependencies? 

A demo version of Pychron Data Reduction aka PyCrunch is now available via a docker image. Checkout [Pychron Docker](https://github.com/NMGRL/pychron_docker) for more details

**NOTE: this is an experimental feature and is likely to evolve over time**

Who's Using Pychron
====================

A number of Ar/Ar Geochronology and noble gas laboratories are using Pychron to various degrees. These include 

 - New Mexico Geochronology Research Laboratory, New Mexico Bureau of Geology
 - University of Manitoba
 - WiscAR, University of Wisconsin
 - SWIRL, US Geological Survey - Denver
 - AGES, Lamont-Doherty Earth Observatory, AGES
 - US Geological Survey - Menlo Park
 - MNGRL, NASA-Goddard Space Flight Center
 - AEL-AMS, Ottawa
 - ANGL, University of Arizona
 
Installation of Pychron at other laboratories is ongoing. Current interested labs are
  
  - University of Florida
  - CAMS, Lawrence Livermore National Laboratory
  - University of Alaska, Fairbanks
  - Arizona State University
  - USGS Reston
  - Geomar
  
Additionally, [Remote Control Server](https://github.com/NMGRL/qtegra), a script made by the pychron developers, is used extensively 
by the international community to interface third-party software with Thermo Scientific's Mass Spectrometer control software.


pyExperiment
--------------
Write and run a set of automated analyses. Allows NMGRL to operate continuously. only limited by size of analysis chamber.

pyCrunch
-------
Display, process and publish Ar-Ar geochronology and thermochonology data. Export publication ready PDF tables and figures. Export Excel, CSV, and XML data tables. Store and search for figures in database.  


pyValve
-----------
Used to control and monitor a noble gas extraction line a.k.a prep system. Displays a graphical interface for user to interact with. A RPC interface is also provided enabling control of the prep system by other applications.

pyLaser
----------
Configure for multiple types of lasers. Currently compatible with Photon machines Fusions CO2, 810 diode and ATLEX UV lasers. Watlow or Eurotherm interface for PID control. Machine vision
for laser auto targeting and modulated degassing.

pyExperiment
--------------
Write and run a set of automated analyses. Allows NMGRL to operate continuously. only limited by size of analysis chamber.

pyCrunch
-------
Display, process and publish Ar-Ar geochronology and thermochonology data. Export publication ready PDF tables and figures. Export Excel, CSV, and XML data tables. Store and search for figures in database.  

furPi
-------
Furnace firmware running on a networked RaspberryPi. RPC interface via Twisted for remote control

Mac OSX 10.9 and Later
--------------------
Mac OSX and macOS operating systems later than 10.9 (Mavericks) include a memory management tool called App Nap. It is necessary to 
turn off App Nap for pychron. 
To turn off App Nap system wide use

    
    defaults write NSGlobalDomain NSAppSleepDisabled -bool YES


# Citing Pychron 
Are you using pychron for data collection and/or data reduction for publishing data? Please cite it by including as much
information as possible from the following: *Jake Ross. (2019). NMGRL/pychron v18.2 (v18.2). Zenodo. https://doi.org/10.5281/zenodo.3237834*
