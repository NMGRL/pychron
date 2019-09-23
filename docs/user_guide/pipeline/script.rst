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
isotopes                  dict   Dictionary of isotopes
isochron3940              ufloat
isochron3640              ufloat
lambda_k                  ufloat
irradiation_label
decay_days
moles_k39
========================= ====== =================

Analysis Methods
====================================== ================== ============= =================
Method                                 Arguments          Return        Description
====================================== ================== ============= =================
get_interference_corrected_value       str                ufloat
get_corrected_ratio                    str, str           ufloat
get_value                              str                ufloat
====================================== ================== ============= =================

.. code-block:: python

    get_interference_corrected_value('Ar40')
    get_corrected_ratio('Ar38', 'Ar36')  # returns Ar38/Ar36 ratio
    get_value('age')  # helper function for getting commonly accessed values


Isotope Attributes
--------------------------
========================= ========= =================
Attribute                 Type      Description
========================= ========= =================
name                      str       Name of the isotope e.g. Ar40
detector                  str       Name of detector used to measure isotope e.g. H1
n                         int       Total number of data points collected. e.g. len(xs)
fn                        int       Total number of data points collected. e.g. len(xs)
offset_xs                 array
xs                        array
ys                        array
fit                       str
value                     float
error                     float
uvalue                    ufloat
baseline                  Isotope
blank                     Isotope
========================= ========= =================

Isotope Methods
------------------------
====================================== ============= =================
Method                                 Return        Description
====================================== ============= =================
get_baseline_corrected_value           ufloat
get_ic_decay_corrected_value           ufloat
get_decay_corrected_value              ufloat
get_interference_corrected_value       ufloat
get_disc_corrected_value               ufloat
get_ic_corrected_value                 ufloat
get_non_detector_corrected_value       ufloat
====================================== ============= =================

Plotting Examples
---------------------------------
Plot with error bars
++++++++++++++++++++++++
.. code-block:: python

    import matplotlib.pyplot as plt
    from uncertainties import nominal_value, std_dev

    def main():

        ns = [a.get_value('Ar40/Ar38') for a in unknowns]
        ds = [a.get_value('Ar40/Ar36') for a in unknowns]

        xs = [nominal_value(di) for di in ds]
        ys = [nominal_value(ni) for ni in ns]

        xerrs = [std_dev(di) for di in ds]
        yerrs = [std_dev(ni) for ni in ns]

        plt.ylabel('Ar40/Ar36')
        plt.xlabel('Ar40/Ar38')

        plt.errorbar(xs, ys, xerr=xerrs, yerr=yerrs, fmt='bo')

        plt.show()

Simple scatter plot
++++++++++++++++++++++++
.. code-block:: python

    import matplotlib.pyplot as plt
    from uncertainties import nominal_value, std_dev

    def main():

        ns = [a.get_value('Ar40/Ar38') for a in unknowns]
        ds = [a.get_value('Ar40/Ar36') for a in unknowns]

        xs = [nominal_value(di) for di in ds]
        ys = [nominal_value(ni) for ni in ns]

        plt.ylabel('Ar40/Ar36')
        plt.xlabel('Ar40/Ar38')

        plt.plot(xs, ys, 'bo')

        plt.show()