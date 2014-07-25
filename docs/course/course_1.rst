Data Reduction
===============

    1. `IsotopeFits`_
    2. `Blanks`_
    3. `ICFactor`_
    4. `Ideogram`_
    5. `Spectrum`_


IsotopeFits
-------------

The first step in data reduction is setting the fit model of the intensity vs time for each isotope.
This is accomplished using the **Isotope Fit** task. You should set the fits for both the unknown analyses
and the reference analyses (i.e. Blanks and Airs)

Blanks
--------
The next step in data reduction is setting the blank values for the unknown and reference analyses.
Setting the blanks is done using the **Blanks** Task

ICFactor
---------
The final step in data reduction is setting the IC factor for the analyses. IC stands for InterCalibration and
typically is used to calibrate a Electron Multiplier (e.g. CDD) detector to a Faraday detector.

.. note:: If you are using a single detector mass spectrometer you would set the **Discrimination** instead of an
IC Factor. Use the **Discrimination** task to set the 1amu detector discrimination.



