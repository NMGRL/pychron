Script
=======================



Access the pipelines state using `state`

e.g.

.. code-block:: python

    unknown_analyses = state.unknowns


for convenience the unknowns are exposed directly via `unknowns`

.. code-block:: python

    #the follow are equivalent
    ans = state.unknowns
    ans = unknowns


Available attributes for analyses

.. code-block::

    # the first analysis in the list
    analysis = unknowns[0]

    # a dictionary of `Isotope` objects
    isotopes = analysis.isotopes

    age = analysis.age

    # age as a `ufloat` object
    uage = analysis.uage

    from uncertainties import nominal_value, std_dev
    age = nominal_value(uage)
    age_err = std_dev(uage)

    # or
    age = analysis.age
    age_w_j_err = analysis.age_err

    # see ArArAge for comprehensive view of the Analysis object

Analysis Attributes
----------------------------
========================= ====== =================
Attribute                 Type   Description
========================= ====== =================
kca                       ufloat  K/Ca
cak                       ufloat  Ca/K
kcl                       ufloat  K/Cl
clk                       ufloat  Cl/K
radiogenic_yield          ufloat  %40Ar*
rad40                     ufloat  40Ar*
total40                   ufloat
k39                       ufloat
uF                        ufloat
F                         float
F_err                     float
F_err_wo_irrad            float
uage                      ufloat
uage_w_j_err              ufloat
uage_w_position_err       ufloat
age                       float
age_err                   float
age_err_wo_j              float
age_err_wo_irrad          float
age_err_wo_j_irrad        float
ar39decayfactor           float
ar37decayfactor           float
========================= ====== =================

Isotope Attributes
--------------------------