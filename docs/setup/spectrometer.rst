Spectrometer
=================

Argus
-----------------

1. Set the values in ``~/Pychron/setupfiles/spectrometer/config.cfg``
 ::

    [General]
    name = jan

    [SourceParameters]
    ionrepeller = 10.0
    electronenergy = 40.20

    [SourceOptics]
    ysymmetry = 50.0
    zsymmetry = 06.0
    zfocus = 70.0
    extractionlens = 01.0

    [Deflections]
    h2 = 0.0
    h1 = 0.0
    ax = 454.0
    l1 = 0.0
    l2 = 0.0
    cdd = 0.0

    [CDDParameters]
    operatingvoltage = 618.0

    [Protection]
    use_detector_protection=True
    detectors=CDD
    detector_protection_threshold=0.1
    use_beam_blank=False
    beam_blank_threshold=0.1

2. Set the mftable.csv. Each value in the table is the peak center in DAC space for a given isotope on a given detector.

.. note :: The DAC value is for a Deflection voltage=0

To populate the table,

    1. set the deflection to zero,
    2. peak center Ar40 on H2
    3. record the DAC value in the approriate cell
    4. repeat 1-3 for Ar40 on H1,AX,..., etc
    5. repeat 1-4 for Ar39,Ar36