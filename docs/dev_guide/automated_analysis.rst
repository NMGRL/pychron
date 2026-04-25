Automated Analysis
---------------------
Automated analysis is handled by ``ExperimentExecutor``, ``ExperimentQueue``, and ``AutomatedRun``.

The runtime is now split between:

- ``ExperimentExecutor`` for UI-facing traits, service wiring, threads, and side effects
- ``ExecutorController`` for executor/queue/run lifecycle decisions
- explicit executor, queue, and run state machines under ``pychron.experiment.state_machines``

ExperimentExecutor
~~~~~~~~~~~~~~~~~~~~
``ExperimentExcecutor`` is the top level object for coordinating automated analyses.
It remains the integration point for panes, Traits events, managers, and persistence side effects,
but queue/run lifecycle policy is progressively moving into the controller and state machines.


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

State Machine Layers
~~~~~~~~~~~~~~~~~~~~~~

The experiment runtime now uses three explicit state layers.

1. ``ExecutorStateMachine``

   - top-level executor lifecycle
   - execute, precheck, running queue, stopping at boundary, cancel, abort, finalize

2. ``QueueStateMachine``

   - one queue lifecycle
   - queue startup, next-run preparation, overlap mode, save waits, shutdown, completion

3. ``RunStateMachine``

   - one run lifecycle
   - create, start, extraction, overlap wait, measurement, post measurement, save, terminal state

Execution Sequence
~~~~~~~~~~~~~~~~~~~~~~

1.  Start button pressed, calls ``ExperimentExecutor.execute``
2.  ``ExperimentExecutor`` drives pre-execute checks and signals the controller
3.  ``ExecutorController`` advances the executor machine into queue execution
4.  A background thread runs ``ExperimentExecutor._execute``
5.  Each queue is started through controller-owned queue lifecycle helpers
6.  A run spec is retrieved from ``new_runs_generator``
7.  ``ExperimentExecutor`` builds an ``AutomatedRun`` from the spec
8.  The controller selects queue run execution mode:

    - ``serial``
    - ``overlap``

9.  ``ExperimentExecutor._do_run`` performs run side effects while the controller owns:

    - run step ordering
    - stop/cancel/abort decisions
    - overlap eligibility
    - queue settle policy
    - queue terminal result selection

10. The run executes the major phases

    a) ``AutomatedRun.start``
    b) extraction
    c) measurement
    d) post measurement
    e) save

11. Queue shutdown and terminal result selection are finalized through controller-owned helpers

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
