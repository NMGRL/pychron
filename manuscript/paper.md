---
title: Pychron: Automated Data Collection and Reduction for Noble Gas and Ar/Ar Geochronology
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
      orcid:
      affiliation: "1, 2"
    - name: Matt Heizler
      orcid:
      affiliation: "1, 2"
affiliations: 
    - name: New Mexico Bureau of Geology
      index: 1
    - name: New Mexico Institute of Mining and Technology
      index: 2
date: 
bibliography: paper.bib
---

# Summary
Software is an essential part of the measurement of noble gases from geologic samples, specifically Ar-Ar geochronology, both for data collection and data processing. Noble gas laboratories use complicated highly customized “Ultra High Vacuum” systems and Magnetic Sector Mass Spectrometers [@mcdougallandharrison:1994] for extracting and measuring the isotopic composition of geologic samples. In the case of Ar-Ar geochronology the ratio of two isotopes of Argon, 40Ar, 39Ar is used to precisely calculate a radiometric date for the sample. The proliferation of inexpensive computing hardware and open source software has greatly benefited Ar-Ar geochronology, allowing for the full automation of the extraction and measurement process. Storage of raw isotopic measurements and metadata in central relational database management systems (RDBMS) such as MySQL have dramatically increased the quality and throughput of analytical data from Ar-Ar facilities. Although software and interfacing with hardware has long been recognized as a critical piece of a laboratory’s infrastructure currently, very little community collaboration exists and many laboratories either lack the full functionality they desire or have unsustainable bespoke solutions. 

Pychron is a fully featured, open source, python-based, data acquisition and processing application for noble gas geochemistry. Developed at New Mexico Geochronology Research Laboratory, Pychron is now being used at a growing number of other Ar-Ar geochronology and noble gas laboratories. Written in python, Pychron uses many standard and third party libraries such as numpy, scipy [@author:2001], uncertainties [@author:2001]
 for computational aspects and Enthought Tool Suite/Qt for a rich customizable UI. 

Pychron supports single and multi-collector automated real-time data collection with mass spectrometers from both Thermo Scientific and Isotopx. Access to legacy data collected using older MAP and Nu instruments is also available. Pychron uses an extensible plugin architecture making it highly configurable and adaptable to various hardware setups. 

The data reduction process is based on a “pipeline” model offering a flexible and configurable workflow for bulk processing data. Pychron uses a custom data management model called “Data Version Control”, that combines a Git-based file versioning system with a relational database. 

We have always envisioned Pychron as a community-based development project and welcome contributions and encourage users to provide feedback, bug reports and feature requests, via GitHub’s issue system at https://github.com/NMGRL/pychron. 


# Mentions
Pychron is used at a growing number of noble gas laboratories throughout North America
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


# Acknowledgements
The work has been supported by NSF EAR XXXX, the New Mexico Bureau of Geology and Mineral Resources and the New Mexico Geochronology Research Laboratory.  

# References