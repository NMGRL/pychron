Automated Analysis
---------------------
Automated analysis is handled by ``ExperimentExecutor``, ``ExperimentQueue``, and ``AutomatedRun``.

ExperimentExecutor
~~~~~~~~~~~~~~~~~~~~
``ExperimentExcecutor`` is a top level object for coordinating the running of automated analyses.


ExperimentQueue
~~~~~~~~~~~~~~~~~~~~
The ``ExperimentQueue`` contains a list of ``AutomatedRunSpec``'s and some global metadata.


AutomatedRunSpec
~~~~~~~~~~~~~~~~~~~~
An ``AutomatedRunSpec`` is a simple container object the holds all of the ``AutomatedRun`` information,
such as labnumber, aliquot, pyscript names, etc.

AutomatedRun
~~~~~~~~~~~~~~~~~~~~~~
The ``AutomatedRun`` contains the top level logic for executing an automated analysis. The ``AutomatedRun``
object is reused and the ``ExperimentExecutor`` has ``measuring_run`` and ``extracting_run`` objects. Two ``AutomatedRun``
objects are required to handle overlap. ``AutomatedRun`` is executed using ``start()``.

Execution Sequence

1.  Start button pressed, calls ``ExperimentExecutor.execute``
2.  pre execute check. ``ExperimentExecutor._pre_execute_check``
3.  New thread started. function= ``ExperimentExecutor._execute``
4.  Each queue in ``ExperimentExecutor.experiment_queues`` is run using ``ExperimentExecutor._execute_queues``
5.  pre run check
6.  runspec retrieved from ``new_runs_generator``
7.  ``AutomatedRun`` updated with runspec data
8.  if overlap new thread started else wait for run to complete return to  step 5
9.  ``ExperimentExecutor._do_run`` starts the ``AutomatedRun``

    a) ``AutoamtedRun._start``
    b) ``AutoamtedRun._extraction``
    c) ``AutoamtedRun._measurement``
    d) ``AutoamtedRun._post_measurement``

PyScripts
~~~~~~~~~~~~~~~~~~~~~~

Pyscript Sequence

    1. Extraction
    2. Measurement
    3. Post Equilibration
    4. Post Measurement

Each script is executed sequentially, except for measurement and post_equilibration.
Post Equilibration and Measurement will be running concurrently after equilibration period
has finished. If a script fails the run is stopped.


Extraction
============
Preforms the extraction of gas. Has access to valves and extraction devices. When finished gas should
be staged for equilibration with the mass spectrometer

Measurement
=============
Performs the measurement of the gas. Has access to valves and mass spectrometer.

Post Equilibration
===================
Pumps out the extraction line following equilibration and isolation of the mass spectrometer
from the extraction line. Has access to the valves.


Post Measurement
===================
Runs after measurement is finished. Typically only pumps out the mass spectroemter.
Has access to the valves.

AutomatedRunPersister
~~~~~~~~~~~~~~~~~~~~~~~
``AutoamtedRunPersister`` is object used to save an analysis to the database.
Uses ``MassSpecDatabaseImporter`` to save to MassSpec schema. ``AutomatedRunPersister``
uses ``IsotopeAdapter`` to save data to Pychron schema

Multiple database backends are handled by the ``DataHub`` and its `stores`. DataHub.main_store
provides access to ``IsotopeAdapter``.

MassSpecDatabaseImporter
=========================

DataHub
~~~~~~~~~~~~~~~~~~~~