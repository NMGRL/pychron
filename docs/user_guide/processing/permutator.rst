Permutator
-------------

Pychron has the ability to automatically generate all data reduction permutations for
a dataset.

.. note:: Currently (dev/2.0.4) only has the isotope evolution permutations implemented.

The permutator is configured using a yaml file. There are two main configuration values the
user must specify.

    1. a list of fit types
    2. (Optional) Ar isotopes to not permutate

The list of fit types defines which fits to permutate for the Ar isotopes.
For example, if the user specifies linear and parabolic the follow permutations are generated.
     ==== ==== ==== ==== ====
     Ar40 Ar39 Ar38 Ar37 Ar36
     ==== ==== ==== ==== ====
     L    L    L    L    L
     L    L    L    L    P
     L    L    L    P    L
     L    L    L    P    P
     L    L    P    L    L
     L    L    P    L    P
     L    L    P    P    L
     L    L    P    P    P
     ...  ...  ...  ...  ...
     P    P    P    P    P
     ==== ==== ==== ==== ====

The total number of permutations equals :math:`n_{fittypes}^5`. If you would like to reduce
the number of permutations you can specify Ar isotopes to skip.



