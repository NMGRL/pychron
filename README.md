Pychron
========

[![Build Status](https://travis-ci.org/NMGRL/pychron.png?branch=develop)](https://travis-ci.org/NMGRL/pychron)
[![Requirements Status](https://requires.io/github/NMGRL/pychron/requirements.png?branch=develop)](https://requires.io/github/NMGRL/pychron/requirements/?branch=develop)
[![Issue Stats](http://issuestats.com/github/nmgrl/pychron/badge/issue)](http://issuestats.com/github/nmgrl/pychron)
[![Gratipay](http://img.shields.io/gratipay/jirhiker.svg)]

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.9884.png)](https://zenodo.org/record/9884#.U3Tp8V4rjfM)

[Changes](CHANGELOG.md)

[Website](http://nmgrl.github.io/pychron/)

[Documentation](http://pychron.readthedocs.org)

[RoadMap](ROADMAP.md)
What is Pychron
===============

Pychron is a set of applications for the collection and processing of noble gas mass spectrometry data. Pychron is developed at the New Mexico Geochronology Research Laboratory at New Mexico Tech. Components of pychron are used within multiple research domains, but mainly for Ar-Ar geochronology and thermochronology. Pychron's main applications are pyValve, pyLaser, pyExperiment and pyView. Additional components include, RemoteHardwareServer RemoteControlServer.cs and Bakedpy. 

Pychron aims to augment and replace the current widely used program Mass Spec by Alan Deino of Berkeley Geochronology Center


pyValve
-----------
Used to control and monitor a noble gas extraction line a.k.a prep system. Displays a graphical interface for user to interact with. A public remote control API is also provided enabling control of the prep system by other applications.

pyLaser
----------
Configure for multiple types of lasers. Currently compatible with Photon machines Fusions CO2, 810 diode and ATLEX UV lasers. Watlow interface for PID control. 

pyExperiment
--------------
Write and run a set of automated analyses. Allows NMGRL to operate continously. only limited by size of analysis chamber. 

pyView
-------
Display, process and publish Ar-Ar geochronology and thermochonology data. Export publication ready PDF tables and figures. Export Excel, CSV, and XML data tables. Store and search for figures in database.  


Mac OSX 10.9
--------------------
Mac OSX 10.9 (Mavericks) includes a memory management tool called App Nap. It is necessary to 
turn off App Nap for pychron. 
To turn off App Nap system wide use

    
    defaults write NSGlobalDomain NSAppSleepDisabled -bool YES
