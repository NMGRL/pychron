Pychron Week Day 3. Fitting IsoEvo, Blanks, ICFactor
======================================================


Review
    1. go over recall
    2. Time View
    3. Added columns to Analyses table (cleanup, duration, etc)
    4. plot an ideogram



Overview
    1. Fit Isotopes
    2. Fit Blanks
    3. Fit IC Factor
    4. View/Diff Blanks History


Fit Isotopes
~~~~~~~~~~~~~~~~~~~~~~

.. attention:: fit isotopes for identifier 61537

.. note:: 61537 is from the Crow project, Irradiation NM-255K

1. Open Iso Evolution Window (*Data>Isotope Evolution*)
2. User browser to locate 61537
3. Use the Controls Pane to select fits to save

.. warning:: If refitting a large number of samples >10 do not plot. **TURN OFF SHOW COLUMN**

4. Hit "Database Save" |dbsave| to save to the database.



Fit Blanks
~~~~~~~~~~~~~~~~~~~~~~

.. attention:: fit blanks for identifier 61537


1. Open the Blanks Window (*Data>Blanks*)

.. note:: Instead of opening a new window you can which to different tasks within the
    same window. For example if you have a Recall Window open switch to the Blanks view
    using *View>Activate Blanks*

2. Add a set of unknowns to the Unknowns Pane. The References Pane will be
   automatically populated with the associated reference analyses (e.g. Blanks)
3. Select the fits from Controls Pane
4. Hit "Database Save" |dbsave| to save to the database

Fit IC Factor
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attention:: fit cdd ic factor for identifier 61537

1. Open the IC Factor Window
2. Add a set of unknowns to the Unknowns Pane
3. Select the reference type from the Controls Pane
4. Select the fits from Controls Pane
5. Hit "Database Save" |dbsave| to save to the database

Viewing Results/Diffing
~~~~~~~~~~~~~~~~~~~~~~~~~

.. |dbsave| image:: ../images/database_save.png
.. |sum_view| image:: ../images/window-new.png
.. |iso_evo| image:: ../images/chart_curve_add.png
.. |diff| image:: ../images/edit_diff.png
          :height: 16px
          :width: 16px
.. |edit| image:: ../images/application-form-edit.png
.. |cog| image:: ../images/cog.png