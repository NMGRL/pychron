Peak Hop Definition
------------------------
This section describes how to define a peak hopping sequence.



A peak hop sequence,``HOPS``, is a list of peak hops (e.i. magnet moves).

::

    HOPS=[('Ar40:H1:10,     Ar39:AX,     Ar36:CDD',      5, 1),
          ('Ar37:CDD',                                5, 1),
          ]


A ``peak hop`` is a list of ``iso:detector`` pairs plus two configuration values,

#. the number of counts at the current position 
#. the settling time (s) after magnet positioning and before measurement starts.

The first ``iso:detector`` pair of each hop is used for positioning.

To specify a non-nominal deflection value for a detector use ``iso:detector:deflection``

::

    Ar40:H1:30

If no value is specified and the deflection value had been changed by a previous cycle
then the deflection is set to the value stored in the spectrometer configuration file.


The following sequence,

::

    ('Ar40:H1,     Ar39:AX,     Ar36:CDD',      10, 1)
    ('Ar40:L2,     Ar39:CDD',                   20, 5)



translates to

#. position Ar40 on detector H1, wait 1s and record 10 H1,AX,and CDD measurements.
#. After 10 measurements position Ar40 on detector L2, wait 5s, then record 20 measurements.


