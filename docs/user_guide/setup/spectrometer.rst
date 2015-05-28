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

2. Set the ``~/Pychron/setupfiles/spectrometer/mftable.csv``. Each value in the table is the peak center in DAC space for a given isotope on a given detector.

   .. note :: The DAC value is for a Deflection voltage=0

   To populate the table,

    1. Set the deflection to zero,
    2. Peak center Ar40 on H2
    3. Record the DAC value in the approriate cell
    4. Repeat 1-3 for Ar40 on H1,AX,..., etc
    5. Repeat 1-4 for Ar39,Ar36

3. Setup the deflection correction files

   1. Create directory ``~/Programming/Pychron/setupfiles/spectrometer/deflections``
   2. For each detector create a text file using the detector name as the name of the file. e.g AX

      .. note:: Use all capital letters and leave off the .txt extension

   3. The detector files are simple csv files where each row represents a ``deflection,dac`` pair. The dac value is
      the voltage required to center a reference isotope (Ar40) on this detector for a given deflection. For example
      the AX file might look like
      ::

        0,6.003672
        135,5.99933

     .. note:: you can add as many calibration points as you like, but in practice the deflection voltages do not
        change over time so you can just define two points, 1) deflection=0 and 2) deflection=<normal operating voltage>
