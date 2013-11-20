Experiments
-------------

This section describes how to write an experiment with Pychron. A pychron ``experiment``
in Mass Spec parlance is a "Multiple Runs Sequence."

Position Rules
~~~~~~~~~~~~~~~

The following is a list of rules for how a position entry is interpreted

#. 4 or p4 (Goto position 4)
#. 3,4,5 (Goto positions 3,4,5. Treat as one analysis)
#. 7-12 (Goto positions 7,8,9,10,11,12. Treat as individual analyses)
#. 7:12 (Same as #3)
#. 10:16:2 (Goto positions 10,12,14,16. Treat as individual analyses)
#. D1 (Drill position 1)
#. T1-2 (Goto named position T1-2 i.e transect 1, point 2)
#. L3 (Trace path L3)
#. 1-6;9;11;15-20 (Combination of rules 2. and 3. Treat all positions as individual analyses)

Here are a few examples of how Rule #9 is processed

::

    user_input=1-6;9
    yields positions= 1,2,3,4,5,6,9


The starting position e.g 1 in the above case can be greater than the end position e.g 6.
::

    user_input=9;6-1
    yields positions= 9,6,5,4,3,2,1

