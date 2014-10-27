Pychron Week Day 2. Browsing
==============================

Browser
------------------------
    1. By Project
    2. By Irradiation
    3. Graphical Filter
    4. Subfilters
    5. Filtering results
    6. Manual Queries

Browsing is a convienent way of navigating the pychron database. It is similar to Mass Spec's recall/run
selection window's however pychron's browser pane has the most commonly used query's predefined and organized
into a simple workflow.

.. note:: If the **Browser** is not open, go to View/Browser. If ``Browser`` is not present then the active window does not support
          the **Browser** and you must open a window that uses it e.g. **Recall**

The browser is laid out in a top down fashion and divided into multiple levels.
    1. Mass Spectrometer
    2. a) Projects
       b) Irradiations
    3. Analysis Types
    4. Date
    5. Results
       a) Sample/Identifier (L#)
       b) Analyses

Filters from the upper levels cascade down to the lower levels. For example selecting Mass Spectrometer=Obama
limits the Projects list to projects that contain analyses from Obama. The same filtering is applied to the
Irradiation list.

.. note:: Use the *Binoculars* button to force a refresh using the current filtering criteria.

Browse By Project
~~~~~~~~~~~~~~~~~~~~
The **Projects** table lists all projects currently in the database.

.. note:: For faster/easier searching of the **Project** table use the **Filter** textbox to limit the displayed projects to projects that begin with the filtering string.
   e.g. filter='abc' projects='abc', 'abcd', 'abcd12' but not '1abc'

.. note:: There are a few special projects listed in the **Projects** table. These are the **RECENT ...** entries, one for each mass spectrometer in the database. Selecting a **RECENT** entry
    will select all samples that have been run within the last *X* hours. To set *X* go to Preferences/Processing/Recent

.. note:: Selecting Projects filters the Irradiation list.

Browser By Irradiation
~~~~~~~~~~~~~~~~~~~~~~~~
Use the Irradiations drop-downs to filter the available samples by irradiation and irradiation level.

.. note:: Selecting an Irradiation Level i.e. "A" filters the Project list.

Subfilters
~~~~~~~~~~~~~~~~
The results from the upper level filters can be further refined with Analysis Type and Date Filters

.. note:: You do not have to start with the top level filters. For example you can start with a Date filter.

Results Tables
~~~~~~~~~~~~~~~~
The results of the filters are displayed in two tables Samples and Analyses. The Samples table
displays all the labnumbers that match your query. Select a set of labnumbers and the Analyses table will
display all the analyses for those labnumbers.

Both the Samples and Analyses tables are filterable. Use the dropdowns to select the attribute to filter on
then enter a value or selected from available options.

.. note:: To configure what columns are displayed hit the "cog" button.

.. note:: By default only labnumbers that have analyses are displayed. To show all labnumbers deselect
   "Exclude Non-run" in the configure dialog (hit the "cog" button)

Recall
-------------------------
    1. Configure View
    2. Isotope Evolution
    3. Edit Data
    4. Split View
    5. History view
       a. diff blanks


Plotting
-------------------------
    1. Ideogram
       a. selecting analyses
            i. double click
            ii. drag and drop
            iii. Append/Replace buttons
