Pychron Introduction
========================

Abstract
-------------
Pychron is a fully featured open source project for automated data collection and processing. The majority of Pychron's
codebase is written using Python, an increasing popular programming language within the scientific and open source
communities.  Pychron is optimized for use with the next generation multi-collector mass spectrometers from Thermo
Scientific. However, Pychron was designed with flexibility and extensibility in mind and application to other hardware
and isotopic systems is readily achievable.

The applications that comprise Pychron use Qt for a modern graphical user interface. GUI's are provided for all major
hardware components such as the mass spectrometer and laser systems, in addition to interfaces for configuring and
executing sequences of automated analyses.

Pychron can save data to a variety of SQL databases such as MySQL and PostgreSQL. Export facilities are available to
translate analysis data and metadata to numerous formats including, XML, CSV, HDF5 and the MassSpec MySQL schema.

Analyses are processed manually using a streamlined workflow. Pychron also provides configurable batch processing
procedures to automate the data reduction process.  Pychron features interactive plots including, time series,
ideograms, spectra, and inverse isochrons. Summary PDF tables following the Renne et al., 2009 format and appendix style
data tables in PDF, CSV or Excel 97-2004 format are generated from easy-to-use dialogs.

Built-in unittests are provided with Pychron to verify the accuracy of the Ar-Ar and other statistical calculations.
Unittests are executed autonomously and continuously using the Continuous Integration service, Travis CI. Documentation
is located at ReadTheDocs.org (https://pychron.rtfd.org). The entire Pychron source code is licensed under the liberal
Apache 2.0 open source license and publicly hosted at GitHub.com (https://github.com/nmgrl/pychron). A beta version of
Pychron is currently available that includes both data acquisition and processing capabilities, identified by the DOI
10.5281/zenodo.9884 (Ross, 2014).



Introduction
------------------
Software has become an essential part of the Ar-Ar geochronology technique, both for data collection and data
processing. The technique has greatly benefited from inexpensive and accessible computing hardware facilitating fully
automated data acquisition.  Storage of raw isotopic measurements and metadata in central relational database management
systems (RDBMS) such as MySQL have dramatically increased the quality and throughput of analytical data from Ar-Ar
facilities. Although software and interfacing with hardware has long been recognized as a critical piece of a
laboratory's infrastructure currently, there exists only one widely used and fully integrated package for Ar-Ar
analysis, Mass Spec by Alan Deino of Berkeley Geochronology Center (BGC). Mass Spec has been of great value to the
community for 20+ years, however we do not consider it a viable and sustainable product for the future in its current
form. Mass Spec does not make use of the many advancements in software development and engineering that have occurred in
the recent past. Mass spec has no adequate version control scheme and relies completely on version numbers for
maintaining a history of changes. No API or extensive documentation is available for Mass Spec, making upgrades, bug
fixes and generic modifications time consuming and inefficient. Mass Spec uses a custom esoteric scripting language for
data collection that greatly limits is flexibility and extensibility. For all of these reasons and more we determined
that a new platform was necessary for sustaining the high quality and highly desired results produced by Ar-Ar
geochronology.

To address many of our concerns with Mass Spec and the general software ecosystem in Ar-Ar geochronology we chose to
develop an open-source and extensible software product named Pychron. Pychron is freely available and makes use of many
recent advancements in software development. It features robust version control via Git and is publicly hosted at
GitHub. Pychron leverages the tremendous efforts of the open-source and scientific communities and uses widely used and
accepted packages such as Numpy, Scipy (Jones et al., 2001) and SQLAlchemy (Bayer, 2006) to ensure sustainability
and efficient design.

The name Pychron is a portmanteau of Python (the main language used for implementation) and Chronology (its main domain
space). We choose Python because of its increasing popularity among the scientific community as well as the web
development community, an area we hope Pychron will benefit from in the near future. Python allows for rapid prototyping
of new features, a critical property for evolving experimental scientific laboratories. As articulated in the Zen of
Python (PEP 20), Python follows the paradigm that code is more often read than written, making it an
ideal language for both novice and advanced programmers, the full range of which is found in the scientific community.
Python's ``batteries included'' concept makes it easy to implement new features, robustly, and when included components
are not adequate an extensive body of open source and proprietary packages are readily available. Python, being an
interpreted language, is often criticized for being too slow. However if computation speed becomes a limiting factor,
algorithms can be implemented using lower level compiled languages, such as Fortran or C, and accessed directly from
python modules. Python tools designed for optimization and speed such as Cython or its predecessor Pyrex provide
additional means to mitigate any speed limitations.

Pychron was specifically designed to operate with Thermo Scientific new generation multicollector mass spectrometers,
notably the ArgusVI. Instead of directly communicating with the ArgusVI's electronics we wrote a lightweight remote
method invocation server in C-sharp, called ``RemoteControlServer.cs``. This relatively simple UDP/TCP server runs
within Thermo's Qtegra environment and facilitates remote control of the mass spectrometer either locally or over a
shared network. The ``RemoteControlServer.cs`` model, over the past 1-2 years has proven itself as a easy and rapid
way to control the new generation of mass spectrometers, allowing users to quickly move from instrument setup and
installation to the end goal of making isotopic measurements. It is installed at numerous noble gas laboratories around
the world and is currently the de facto method for interfacing third party software with Qtegra.

Running Pychron on any system is achievable by a variety of mechanisms. A simple entry point script is provided for
developers to launch from the command-line or their preferred IDE (Integrated Development Environment). For end users, a
self-contained application is constructed using a built-in python script called ``app_maker.py.`` The resulting
application bundle allows the user to launch from the dock or start menu.  (Currently ``app_maker.py``  is only
setup for Mac OSX, but variants for Windows and Linux are possible)
