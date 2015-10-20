Conditionals
=================

Conditionals are the pychron mechanism used to take action if a given condition evaluates to True, e.g.
age>2.0. There are three levels of Conditionals 1) System 2) Queue 3) Run. System conditionals are applied to every
run of every experiment. A typical system conditional is to cancel the experiment if the CDD is not on/enabled.
Queue Conditionals can be specified per experiment queue. Queue conditionals are applied to all runs in the experiment.
Run conditionals are specified on a per run basis. There is also multiple types of conditionals. System and Queue
conditionals fall into five categories 1) Actions, 2) Pre Run Terminations 3) Truncations 4) Terminations and
5) Post Run Terminations. Run conditionals have all the same categories except for Pre and Post Terminations.

Truncations conditionals truncate the current run (curtail in MassSpec parlance) and do an abbreviated baseline measurement.
Terminations cancel the experiment immediately. Actions allow you to specify a action to take such as run a blank, etc. Custom
actions can be programmed using pyscripts.

Levels
-----------

================ ==========================
Name             Description
---------------- --------------------------
System           Executed for all runs in all experiment queues
Queue            Executed for all runs in this experiment queue
Run              Executed for only this run
================ ==========================

Conditional Types
-------------------
=================== ==========================
Name                Description
------------------- --------------------------
Action               Executed for all runs in all experiment queues
Truncation            Executed for all runs in this experiment queue
Termination              Executed for only this run
Cancelation
PreRunTermination
PostRunTermination
=================== ==========================


Functions/Modifiers
--------------------
.. note:: User supplies the values contained in brackets (i.e. ``[ ]``)

================================== =============================================== ====================================
Name                               Description                                     Example
---------------------------------- ----------------------------------------------- ====================================
min([value])                                                                       min(Ar40)
max([value])                                                                       max(Ar40)
average([value])                                                                   average(Ar40)
slope([value])                                                                     slope(Ar40)
[name].current                     get the last measured intensity for an isotope  Ar40.current
[name].cur                         same as current                                 Ar40.cur
device.[name]                      get a device value                              device.pneumatics
[controller].[gauge].pressure      get a pressure from an controller               bone.ig.pressure
[name].deflection                  get detector's deflection                       H1.deflection
[isotope]/[isotope]                get a baseline corrected ratio                  Ar40/Ar36
between([value], [v1],[v2])        check if a value is between v1,v2               between(max(Ar40), 10, 100)
not                                invert logic                                    not Ar40<100
================================== =============================================== ====================================

Writing Conditionals
----------------------
There is a primitive GUI for editing AutomatedRun Conditionals. You can probably get away with using the GUI 95% of the time,
however, there are a few cases that are not currently implemened in the GUI, but nevertheless maybe used by editing the specific
conditionals file. All conditional files use standard yaml syntax. Here is an example system_conditionals.yaml

.. code-block:: YAML

    actions: []
    pre_run_terminations:
     - check: CDD.inactive
     - check: CDD.deflection==2000
     - check: bone.ig.pressure > 1e-8
     - check: microbone.ig.pressure > 1e-8
     - check: device.pneumatics < 10
    post_run_terminations:
     - check: Ar40 < $MIN_INTENSITY
       analysis_types:
        - air
        - cocktail
    terminations: []
    truncations: []


Notice the special syntax used for the only Post Run Termination (Ar40 < $MIN_INTENSITY). This is the interpolation/templating syntax.
The interpolation syntax ($VARIABLE_NAME) is used to define the conditional's sentinel values at runtime. For instance
the above post run termination conditional terminates the experiment if an Air's Ar40 intensity is below a certain threshold.
The reason for interpolating the minimum intensity is that this value is dependent on the extraction script, e.i. either a
full air shot or a sniff air. To specify an interpolatable value simply assign the variable in the extraction scripts metadata
docstring.

.. code-block:: Python

    '''
    sensitivity_multiplier: 0.5
    modifier: 1
    MIN_INTENSITY: 10
    '''
    def main():
        info('Jan Air Script')


In this case, the Post Run termination conditional would trip if the Ar40 intensity was less the 10 fA.