Pychron Week Day 1. General Pychron/Experiment
================================================

Pychron Week Day 1. 10/26/14

The topics covered today will be general pychron information and new experiment features.

General
-------------
    1. Preferences
    2. View Docs
    3. Submit Issue/Lab note
       a) github navigation
       b) gists
    4. Window/Pane layouts

Lets start by going of some general pychron topics. First we will examine pychron's preferences.
The preference window will open as drawer from the currently active window. When open you will
see multiple tabs. There is typically one tab per plugin. With in each tab there maybe subgroups and subtabs.
Sometimes the preference window is too small, so feel free to resize it. There are two important preference tabs
to be aware of as an end-user, Database and Processing

Preferences
-----------------

Database
~~~~~~~~~~~~~~~
The database tab allows you configure which database you would like to connect to. A set of connection favorites
may also be stored for easy switching between databases.


Processing
~~~~~~~~~~~~~~~
The processing tab contains misc preference values used during browsing and processing analyses. For now lets
just set Recent Hours to some value, say 12.


Viewing Documentation
----------------------
The pychron documentation is hosted online at pychron.readthedocs.org. You can access this course material in
addition to a user and developer guide, by navigating to pychron.readthedocs.org in your browser or from pychron's
Help menu. This is the first place to look for information about pychron. It currently is poorly populated but will
evolve and expand as time passes, feedback is received and new features are available.

The documentation is also specific to individual pychron versions, so if you are using an outdated pychron make sure
to navigate to the current documentation. The documentation follows the same numbering scheme as the application. For
example documentation for pychron-v2.0.4 (the current beta release) is found at documentation version release-v2.0.4.
pychron.readthedocs.org will bring you to the latest version of pychron (i.e the develop branch).

Submitting Issues
--------------------
Reporting bugs, requesting features, asking questions, etc... view GitHub's issuetracking system is an efficient (and
recommended) method for communicating with the pychron developers. To submit an issue go to the help menu and
select Add Request/Report Bug. This will open a browser window and navigate to pychron's github repository. If you are not
automatically signed in, sign in with your account info or use the labs generic account nmgrluser, argon4039. I would prefer
you each obtain a user account and use it when ever submitting issues because this allows better tracking/notification and
your issue is more likely to be handled promptly by a developer.

If you submit an issue and want to include code snippets (e.g. lines from pyscripts) or sections of the log file make sure
to surround the text with three backticks (```)

.. code:: python

    ```
        peak_hop(hops)
    ```

Experiment
-----------------
    1. End After
    2. Time At
    3. Open Last Experiment
    4. Username/Email
    5. Conditionals
      a) system
      b) queue
      c) run
    6. wait dialog
       a) extending the total time
    7. Auto comment

Script Editing
-----------------
    1. Context Editor
    2. Visual Script Editor

Labnumber Entry
-----------------
    1. Import irradiations from MassSpec
    2. Manual Entry/Editing

Loading Entry
------------------

Spectrometer
------------------
    1. rise rate
    2. peak center
    3. reset graph

Extraction Line
-------------------
    1. Procedures
    2. Sample loading

Laser
-------------------
    1. Patterning