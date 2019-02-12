ArAr Age Calculations
=======================

F-valve Calculation
----------------------
.. code-block:: python

    # user supplied values
    # ic/decay corrected intensities
    a40=  #Ar40
    a39=  #Ar39
    a38=  #Ar38
    a37=  #Ar37
    a36=  #Ar36
    k4039= #(40/39)K production ratio
    ca3937= #(39/37)Ca
    k3739= #(37/39)K
    k3839= #(38/39)K
    ca3637= #(36/37)Ca
    ca3837= #(38/37)Ca
    cl3638= #(36/38)Cl
    lambda_cl36= # Cl36 decay constant
    decay_time= # time since irradiation
    atm3836 = # trapped Ar38/Ar36
    trapped_4036= # trapped Ar40/Ar36

    # ca-correction
    # iteratively calculate 37, 39
    k37 = 0
    for _ in range(5):
        ca37 = a37 - k37
        ca39 = ca3937 * ca37
        k39 = a39 - ca39
        k37 = k3739 * k39

    k38 = k3839 * k39

    ca36 = ca3637 * ca37
    ca38 = ca3837 * ca37


    # cl-correction
    m = cl3638 * lambda_cl36 * decay_time

    atm36 = 0
    for _ in range(5):
        ar38atm = atm3836 * atm36
        cl38 = a38 - ar38atm - k38 - ca38
        cl36 = cl38 * m
        atm36 = a36 - ca36 - cl36


    atm40 = atm36 * trapped_4036

    k40 = k39 * k4039

    rad40 = a40 - atm40 - k40
    f = rad40 / k39


Age Calculation
----------------------

.. code-block:: python

  lambda_k =  # total 40K decay constant
  f = # F-value e.g Ar40*/Ar39K
  j = # J-value e.g. neutron flux parameter
  age = lambda_k ** -1 * ln(1 + j * f))


Apply Fixed (37/39)K
--------------------------

.. code-block:: python

   """
        x=ca37/k39
        y=ca37/ca39
        T=s39dec_cor

        T=ca39+k39
        T=ca37/y+ca37/x

        ca37=(T*x*y)/(x+y)
    """

    k3739 = # (37/39)K
    ca39 =  # (39/37)Ca

    x = k3739
    y = 1 / ca3937

    ca37 = (a39 * x * y) / (x + y)

    ca39 = ca3937 * ca37
    k39 = a39 - ca39
    k37 = x * k39


Decay Factors
---------------------
.. code-block:: python

    """
        McDougall and Harrison
        p.75 equation 3.22

        the book suggests using ti==analysis_time-end of irradiation segment_i

        mass spec uses ti==analysis_time-start of irradiation segment_i

        using start seems more appropriate
    """

        dc37 = # Ar37 decay constant
        dc39 = # Ar39 decay constant

        a = sum([pi * ti for pi, ti, _, _, _ in segments])

        b = sum([pi * ((1 - math.exp(-dc37 * ti)) / (dc37 * math.exp(dc37 * dti)))
             for pi, ti, dti, _, _ in segments])

        c = sum([pi * ((1 - math.exp(-dc39 * ti)) / (dc39 * math.exp(dc39 * dti)))
             for pi, ti, dti, _, _ in segments])


        df37 = a / b
        df39 = a / c




Abundance Sensitivity
--------------------------

.. code-block:: python

    s40 = # m/e=40 intensity


    # correct for abundance sensitivity
    # assumes symmetric and equal abundant sens for all peaks
    n40 = s40 - abundance_sensitivity * (s39 + s39)
    n39 = s39 - abundance_sensitivity * (s40 + s38)
    n38 = s38 - abundance_sensitivity * (s39 + s37)
    n37 = s37 - abundance_sensitivity * (s38 + s36)
    n36 = s36 - abundance_sensitivity * (s37 + s37)