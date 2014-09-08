Import Analyses From File
----------------------------

It is possible to import analyses from a Excel, csv, or yaml file into the pychron database.

Excel
~~~~~~~
To import analyses from an Excel file follow the following file format.

.. note:: Column order is not important, however, column names must match the following table. In addition the column names
should be on the second row.

Example Excel template

:download:`analysis_import.xls`

Necessary Columns

=============================== =============================== =============================== ================= ===============================================================
name                            type                            example                         optional          note
=============================== =============================== =============================== ================= ===============================================================
identifier                      str                             12345
project                         str                             Foo
sample                          str                             Bar
material                        str                             Feldspar
aliquot                         int                             1
step                            int or str                      2 or B
analysis_type                   str                             unknown
mass_spectrometer               str                             jan
analysis_time                   date                            6/7/12
irradiation                     str                             NM-256                           Yes
comment                         str                             This is a comment                Yes
Ar40                            str or float                    10.123 or Sheet2                                    Use sheet name to link to sheet with raw data
Ar40err                         str or float
Ar39                            str or float
Ar39err                         str or float
Ar38                            str or float
Ar38err                         str or float
Ar37                            str or float
Ar37err                         str or float
Ar36                            str or float
Ar36err                         str or float
Ar40bs                          str or float
Ar40bserr                       str or float
Ar39bs                          str or float
Ar39bserr                       str or float
Ar38bs                          str or float
Ar38bserr                       str or float
Ar37bs                          str or float
Ar37bserr                       str or float
Ar36bs                          str or float
Ar36bserr                       str or float
Ar40bk                          float
Ar40bkerr                       float
Ar39bk                          float
Ar39bkerr                       float
Ar38bk                          float
Ar38bkerr                       float
Ar37bk                          float
Ar37bkerr                       float
Ar36bk                          float
Ar36bkerr                       float
Ar40det                         str
Ar39det                         str
Ar38det                         str
Ar37det                         str
Ar36det                         str
=============================== =============================== =============================== ================= ===============================================================
