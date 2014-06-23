Pychron and the Spectrometer
=============================

.. toctree::
:maxdepth: 2

       measurement_script

Source Parameters
-----------------------------

There are three ways in which pychron can interact with the spectrometers sources
settings. 

1. **Readonly** - Pychron only reads the sources parameters from the spectrometer. 
   For each analysis these values are saved to the pychron database in the ``meas_SpectrometerParametersTable``.
   
   **!Pychron currently does not save the source values to the secondary database.!**
   
2. **Read/Write** - Pychron sets the source parameters in the **measurement** script. By using a pyscript
   the user has fine-grained control of when and what values are set. 
   See below for detailed description of setting source parameters in a pyscript.
3. **Config Write** - On startup Pychron sets the source parameters using values 
   retrieved from a configuration file located at ``setupfiles/spectrometer/config.py``
    

Setting Source parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~
Set source parameters individually by name ::
    
    set_extraction_lens(103.4)

Set parameters using a configuration file located at
``setupfiles/spectrometer/config.py`` ::

    set_source_parameters()
    set_source_optics()   

Values from the configuration file can be overwritten by specifying a parameter name and value ::

    set_source_parameter(IonRepeller=134)
    
 
Detector Parameters
-----------------------------
Interacting with the detector parameters is the same as with the source parameters. 
The deflection values are saved in the pychron database in the ``meas_SpectrometerDeflectionsTable``


Reference
-----------------------

Pyscript Commands
~~~~~~~~~~~~~~~~~~~~~
::
    
    set_ysymmetry(100)
    set_zsymmetry(100)
    set_zfocus(100)
    set_extraction_lens(100)
    set_deflection('H2',0)
    
    # IonRepeller, ElectronVolts
    set_source_parameters()
    
    # ExtractionLens, YSymmetry, ZSymmetry, ZFocus
    set_source_optics()

Config file Example
~~~~~~~~~~~~~~~~~~~~~~~~~
::
    
    [SourceParameters]
    ionrepeller = 0
    electronvolts = 0
    
    [SourceOptics]
    ysymmetry = 0
    zsymmetry = 0
    zfocus = 0
    extractionlens = 0
    
    [Deflections]
    h2 = 0
    h1 = 0
    ax = 0
    l1 = 0
    l2 = 0
    cdd = 0
    
    [CDDParameters]
    operatingvoltage = 618.0
    
        


    


