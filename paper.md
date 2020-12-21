---
title: 'Pychron: Automated Data Collection and Reduction for Noble Gas Geochemistry and Ar/Ar Geochronology'
tags:
  - python
  - geochronology
  - geoscience
  - noble gas 
authors:
  - name: Jake Ross 
    orcid: 0000-0003-4727-7472 
    affiliation: "1, 2"
  - name: William McIntosh 
    orcid: 0000-0002-5647-2483 
    affiliation: "1, 2"
  - name: Matthew Heizler 
    orcid: 0000-0002-3911-4932 
    affiliation: "1, 2"
affiliations:
  - name: New Mexico Bureau of Geology 
    index: 1
  - name: New Mexico Institute of Mining and Technology 
    index: 2 
date: 15 December 2020 
bibliography: paper.bib
---

# Summary

Software is an essential part of the extraction, measurement, data collection, and data processing of noble gases from
geologic samples. Noble gas laboratories use highly customized ultra-high vacuum systems and mass spectrometers for
extracting and measuring the isotopic composition of geologic samples. Pychron was originally developed for Ar-Ar
geochronology, where the ratios of five isotopes of argon are measured to precisely calculate the geologic age or
thermal history of the sample.

# Statement of need

The proliferation of inexpensive computing hardware and open source software has greatly benefited noble gas
geochemistry, allowing for the full automation of the extraction and measurement process. Storage of raw isotopic
measurements and metadata in central relational database management systems (RDBMS) such as MySQL have dramatically
increased the quality and throughput of analytical data from Ar-Ar facilities.

Although software has long been recognized as a critical element of noble gas laboratory infrastructure, little
community collaboration currently exists to develop and maintain robust, functional and sustainable software. Many
laboratories either lack the full functionality they desire or have unsustainable custom solutions.

# Description 

Starting in 2008, Pychron has been under developed at New Mexico Geochronology Research Laboratory, forming the basis
for a sustainable software ecosystem for noble gas geochemistry. Pychron is a fully featured, open source, python-based
application used for data acquisition and processing in noble gas geochemistry and is now being used at a growing number
of laboratories around the world. Written in python, Pychron uses many standard and third party libraries such as
numpy [@2020NumPy-Array:2020], scipy [@2020SciPy-NMeth:2020], uncertainties [@lebigot2010uncertainties:2010]
for computational aspects and Enthought Tool Suite/Qt for a rich customizable UI.

Pychron supports single and multi-collector automated real-time data collection with mass spectrometers from Thermo
Scientific, Isotopx and Pfeiffer and is readily adapted to other instruments. Legacy data collected using older MAP and
Nu instruments is accessible via Pychron. Pychron uses an extensible plugin architecture making it highly configurable
and adaptable to various hardware setups.

The data reduction process is based on a “pipeline” model offering a flexible and configurable workflow for bulk
processing data. Pychron uses a custom data management model called “Data Version Control”, that combines a Git-based
file versioning system with a relational database.

We have always envisioned Pychron as a community-based development project and welcome contributions and encourage users
to provide feedback, bug reports and feature requests, via GitHub’s issue system at https://github.com/NMGRL/pychron.

# Active Laboratories
Pychron is used at a growing number of noble gas laboratories throughout North America.

 - New Mexico Geochronology Research Laboratory, New Mexico Bureau of Geology
 - University of Manitoba
 - WiscAR, University of Wisconsin
 - SWIRL, US Geological Survey - Denver
 - AGES, Lamont-Doherty Earth Observatory, AGES
 - US Geological Survey - Menlo Park
 - MNGRL, NASA-Goddard Space Flight Center
 - AEL-AMS, Ottawa
 - ANGL, University of Arizona
 - TAP, Purdue University
 - HAL, University of Indiana Urbana-Champaign
 - University of Florida


# Acknowledgement
The work has been supported by NSF EAR 1460534, the New Mexico Bureau of Geology and Mineral Resources and the New Mexico Geochronology Research Laboratory.  

# References