Using the Browser
-------------------

The **Browser** is a convenient way of navigating the pychron database.

.. note:: If the **Browser** is not open, go to View/Browser. If ``Browser`` is not present then the active window does not support
          the **Browser** and you must open a window that uses it e.g. **Recall**

The first step when using the **Browser** is to select a top-level filtering criteria. These are

  1. Projects
  2. Irradiation/Level

.. note:: Irradiation/Level is only enabled when no Projects are selected. To clear the project selection, Right-click/Unselect or use the **X** button

The **Projects** table lists all projects currently in the database.

.. note:: For faster/easier searching of the **Project** table use the **Filter** textbox to limit the displayed projects to projects that begin with the filtering string.
   e.g. filter='abc' projects='abc', 'abcd', 'abcd12' but not '1abc'

.. note:: There are a few special projects listed in the **Projects** table. These are the **RECENT ...** entries, one for each mass spectrometer in the database. Selecting a **RECENT** entry
    will select all samples that have been run within the last *X* hours. To set *X* go to Preferences/Processing/Recent


Use the Irradiations drop-downs to filter the available samples by irradiation and irradiation level.

.. note:: Use the *Binoculars* button to force a refresh using the current filtering criteria.


Graphical Filtering
~~~~~~~~~~~~~~~~~~~
The Graphical Filtering view provides a way to view and select a series of analyses. You can narrow that date range to display in a number of ways

    1. Hit the Graphical Filtering button and select a date range manually
    2. Select a set of projects and pychron automatically selects the start and end dates
    3. Select a set of projects then fine tune your selection of samples

.. note:: If the date range is greater than *X* days you are asked to fine tune your selection by modifying the start and/or end dates. To set *X* go to Preferences/Processing/Graphical Filtering
.. note:: If the samples you have selected were run on multiple mass spectrometers you are given the option of filtering the selection by mass spectrometer.

Advanced Filtering
~~~~~~~~~~~~~~~~~~

If you find that the **Browser** cannot filter the analyses in the desired way, you may use the **Advanced Filtering** option.
This will open a dialog similar to **Mass Spec's** run selection, in which you may string together a list of queries in order to search for
a set of analyses