Import Samples From File
----------------------------

It is possible to import analyses from a Excel

Excel
~~~~~~~
To import samples from an Excel file follow the following file format.

.. note:: Column order is not important, however, column names must match the following table.
          In addition the column names should be on the second row.

Example Excel template

:download:`sample_import.xls`

Necessary Columns

=============================== =============================== =============================== ================= ===============================================================
name                            type                            example                         optional          note
=============================== =============================== =============================== ================= ===============================================================
sample                          str                             foo-001
project                         str                             Bar
material                        str                             Feldspar
=============================== =============================== =============================== ================= ===============================================================
