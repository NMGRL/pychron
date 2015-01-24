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
================ ===========================

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
=================== ===========================
