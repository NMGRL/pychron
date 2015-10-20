Pychron Week Day 1. General Pychron/Experiment
================================================

Pychron Week Day 1. 10/26/14

The topics covered today will be general pychron information and new experiment features.

General
-------------
    0. Launching
    1. Preferences
    2. View Docs
    3. Submit Issue/Lab note
       a) github navigation
       b) gists
    4. Window/Pane layouts

You can launch pychron in one of three ways
    1. terminal
    2. pycharm/IDE
    3. icon

Launch from the terminal

.. code:: python

    >> cd /path/to/pychron/source
    >> python launchers/pyexperiment.py

Launch from PyCharm
    Go to the top tool bar and hit the "Play" button, a green triangle.

Launch from Icon
    Double click the pychron icon an launch like any other application

    .. note:: Not all computers have the application icons. Today we will be running from pycharm on the lab computers
    and the terminal on personal labtops.

Lets start by going over some general pychron topics. First we will examine pychron's preferences.
The preference window will open as a drawer from the currently active window. When opened you will
see multiple tabs. There is typically one tab per plugin. Within each tab there maybe subgroups and subtabs.
Sometimes the preference window is too small, so feel free to resize it. There are two important preference tabs
to be aware of as an end-user, Database and Processing

Preferences
-----------------

Database
~~~~~~~~~~~~~~~
The database tab allows you to configure which database you would like to connect to. A set of connection favorites
may also be stored for easy switching between databases.

.. attention:: Lets go over setuping up a database connection together.


Processing
~~~~~~~~~~~~~~~
The processing tab contains misc preference values used during browsing and processing analyses.

.. attention:: set Recent Hours to some value, say 12.


Viewing Documentation
----------------------
The pychron documentation is hosted online at pychron.readthedocs.org. You can access this course material in
addition to a user and developer guide, by navigating to **pychron.readthedocs.org in your browser or from pychron's
Help menu**. This is the first place to look for information about pychron. It currently is poorly populated but will
evolve and expand as time passes, feedback is received and new features are available.

.. caution:: The documentation is also specific to individual pychron versions, so if you are using an outdated pychron make sure
    to navigate to the current documentation. The documentation follows the same numbering scheme as the application. For
    example documentation for pychron-v2.0.4 (the current beta release) is found at documentation version release-v2.0.4.
    pychron.readthedocs.org will bring you to the latest version of pychron (i.e the develop branch).

.. attention:: Practice going to the documentation page. Practice navigating around the documentation. Use the next and previous
   buttons, click on links, use the table of contents. **Extra** View different versions of the documentation


Submitting Issues
--------------------
Reporting bugs, requesting features, asking questions, etc... via GitHub's issuetracking system is an efficient (and
recommended) method for communicating with the pychron developers. To submit an issue go to the help menu and
select Add Request/Report Bug. This will open a browser window and navigate to pychron's github repository. If you are not
automatically signed in, sign in with your account info or use the labs generic account nmgrluser, argon4039.

.. important:: I would prefer you each obtain a user account and use it when ever submitting issues because this allows better tracking/notification and
    your issue is more likely to be handled promptly by a developer.

If you submit an issue and want to include code snippets (e.g. lines from pyscripts) or sections of the log file make sure
to surround the text with three backticks (```)

.. code:: python

    ```
        peak_hop(hops)
    ```

.. attention:: Practice navigating around github. Go to NMGRL/Laboratory repo and practice submitting bugs. Include a code
    block and use preview. Add a label.


Experiment
-----------------
    1. End After/Skip
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
    8. Jump/Move To
    9. Run blocks

**End After** is a convenient feature that allows you to stop the experiment after a selected analysis, instead of
the current analysis using the "Stop at Completion" checkbox. The background will be dark gray when you
set the experiment to end after the selected analysis.

**Skip** is a convenient feature that allows you to skip selected runs. This feature is rarely needed but nonetheless is
available. Skipped runs will have a light blue background color.

.. attention:: You can toggle both End After and Skip by selecting a set of runs and using the checkboxes in the Experiment editor or
    by right clicking.

**Time At.** While an experiment is running you can selected a enqueued run and get the estimated time at
which this analysis will run.

**Open Last Experiment** The **Open Last Experiment** menu action opens the last experiment that was executed.

**Username/Email** When writing an experiment make sure to set the username. A list of users and associated emails
is stored in the database and available via the username drop-down widget. If your username is not in the drop-down
simply type in any name you wish. If you supply an email address pychron will email you when
the experiment completes or is canceled.

**Conditionals** Conditionals are the pychron mechanism used to take action if a given condition evaluates to True, e.g.
age>2.0. There are three levels of Conditionals 1) System 2) Queue 3) Run. System conditionals are applied to every
run of every experiment. A typical system conditional is to cancel the experiment if the CDD is not on/enabled.
Queue Conditionals can be specified per experiment queue. Queue conditionals are applied to all runs in the experiment.
Run conditionals are specified on a per run basis. There is also multiple types of conditionals. System and Queue
conditionals fall into five categories 1) Actions, 2) Pre Run Terminations 3) Truncations 4) Terminations and
5) Post Run Terminations. Run conditionals have all the same categories except for Pre and Post Terminations.

Truncations conditionals truncate the current run (curtail in MassSpec parlance) and do an abbreviated baseline measurement.
Terminations cancel the experiment immediately. Actions allow you to specify a action to take such as run a blank, etc. Custom
actions can be programmed using pyscripts.

.. attention:: Practice adding a simple and a path truncation to some runs.

**Wait Dialog** You should be familiar with the basic concepts of the Wait Dialog. One feature that has not been discussed
in depth is "Set Max Seconds." This is used to extend the wait period beyond the original time. For example say the wait dialog
starts at 30 seconds but you are doing something and want to delay 5 minutes. Enter 300 into "Set Max Seconds" and the wait
dialog will reset to 300 seconds.

**Auto comment** Comments are a useful feature for bookkeeping and keeping things straight during data reduction. A typical
comment for Monitor data is the irradiation level and hole e.g. A:9. Instead of have to type this manually for each labnumber
pychron provides an auto comment feature. Simply check the checkbox to auto fill the comment. There is also an option to generate
your own comment templates. For example the template "irrad_level : irrad_hole SCLF" when applied to a given labnumber would
yield "A:9 SCLF".

.. attention:: Try using the auto comment feature.

.. note:: The template feature is not available for the pyexperiment version on the lab computers.

**Jump/Move To** Right click on a run and select move to or jump to... move to... will move the selected rows to
the specified location. jump to... will move the specified location into view.

.. attention:: Try the jump/move to features

**Run Blocks** provide a mechanism to save commonly used sequences of runs. To save a run block, select the set of runs,
right click and select "Make Run Block". To add a run block select it from the drop down in the Experiment Editor and
hit the add button. You don't have to save a run block if its a one off. You can repeat a selected set of runs by right
clicked and selecting "Repeat Run Block". This will repeat the selected runs, a "run block", every X runs. "Repeat Run Block"
will ask for the value of X.

.. attention:: Practice using the "Run Block" features


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