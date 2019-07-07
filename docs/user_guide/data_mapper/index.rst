Data Mapper
=================


USGS Menlo (Volcano Science Center)
------------------------------------

Importing analyses and metadata into pychron

1. Import Irradiation

    - Menubar> Entry> Import Irradiation...
    - Select USGSVSC MAP
    - Click the Folder icon and select the appropriate irradiation file
    - Click "Import" to import the selected irradiation file

    example Irradiation File

.. code-block:: none

    IRR330
    09/23/2014, 1 hour TRIGA, Cd shielded, use average 04/2011 values
    steps	1
    1.0	3494329980	1
    36/37	2.810000E-4	6.210000E-6
    40/39	1.003000E-3	3.790000E-4
    39/37	7.100000E-4	4.960000E-5
    38/37	3.290000E-5	7.500000E-6
    38/39	1.314000E-2	1.200000E-5

2. Import Analyses

    Analyses can be imported either individually (file) or as a group (directory)

    - Menubar> Entry> Import Analyses
    - Select USGSVSC MAP  from the first drop down
    - Select a Repository Identifier. You can also add a repository using the (+) button
    - Select either an entire directory or an individual analysis file to import.
    - Click "Import" to import analyses