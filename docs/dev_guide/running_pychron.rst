Launching Pychron
===================

Envisage
----------

All pychron applications are based on Enthought's envisage application framework. The envisage framework is used to make pychron extensible and pluggable.
For more information see http://docs.enthought.com/envisage/

Entry Point
-----------

The entry point for all pychron applications are scripts located in the ``launchers`` package. For example, to launch
pyexperiment ::

    cd pychron
    python launchers/pyexperiment.py

This script calls imports and calls ``entry_point`` from the ``helpers`` module.

The ``entry_point`` function performs multiples tasks.

    1. sets the GUI backend to Qt ``ETSConfig.toolkit = "qt4"``
    2. updates the pythonpath
    3. sets global variables and pychron filesystem paths
    4. constructs missing directories in Pychrondata...
    5. sets up logging
    6. calls the ``launch`` function

The ``launch`` function takes one argument, a PychronApplication class. The ``launch`` function is located at ``pychron.envisage.pychron_run``.

``launch`` does the following

    1. checks that necessary dependencies are installed
    2. constructs the application object using ``app_factory``
    3. launches the application by calling the application's ``run`` method

During Step. 2 the necessary plugins are constructed and added to the application. The plugins to use are specified in the ``initialization.xml`` file.
Parsing of the ``initialization.xml`` file is handled by an ``InitializationParser`` object.



Initialization
----------------
If **Hardware** plugins are included, such as **FusionsCO2**, the **HardwarePlugin** is added to the application plugins.
When the **HardwarePlugin** starts, it uses an ``Initalizer`` object to bootstrap the necessary managers and devices.


