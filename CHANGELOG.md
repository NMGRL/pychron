CHANGELOG
============
2.1.1
------------------
### Features ###

### Bug Fixes ###


2.1.0
------------------

### Features ###
* added level and chronology panes to Labnumber entry
* added padding to plot options
* added database version check to startup tests
* !SubMajor Version Bump! Changed to a global shared browser model for all processing tasks
* added Legend to Spectrum
* added ability to display Sample/Identifier in Plateau
* updated export task
* added sqlite export
* added sqlite access
* added ability to edit plateau criteria
* added forced plateau
* added legend to Spectrum
* added table view to Figure Task. Use "New Table" action in toolbar
* added ranking to incremental heat templates. list top ten used templates for a user

#### 2/3/2015 ####
* removed mswd from integrated age
* added ability to control plateau envelope/line color
* spectrum labels match envelope color
* display number of analyses as n/m if n != m. n = # of valid analyses, m = total # of analyses
* added group attributes to spectrum options. allows you to set color for group and calculate a fixed plateau for a specific group

#### 2/5/2015 ####
* added inset to inverse isochron

#### 2/7/2015 ####
* added analysis number aux plot to ideogram inset
* added edit view to aux plots. edit marker and marker size

#### 2/10/2015 ####
* added history limit to sqlite export. transfer the last n histories. defaults to 1. so only transfer the latest history

#### 2/14/2015 ####
* started system health concept. analyze a time series and take action

#### 2/18/2015 ####
* added "Run Startup Tests" to help menu
* added "Select Unknowns" to experiment queue context menu
* started formatting modes e.g Screen, Presentation, Publication, etc. each mode has an associated set of fonts.
* added AxisTool. Right click on a axis to edit it. 

#### 2/20/2015 ####
* added a new Magnet Scanner. Use rulers to set limits. 

#### 3/8/2015 ####
* added Display to formatting modes
* updated system monitor
* added separate figure options for system monitor
* cleaned up Figure UI
* added No Intensity change check to startup tests and scan manager
* added superscript/subscript plot labels
* added manual entry load name. A load name is now required now if an extraction device is set. 
* updated estimated duration calculation
* added Random Tip on startup
* added use_advanced_ui option.  if false displays a stripped down ui (currently just displays a subset of the Menubar actions)

#### 3/10/2015 ####
* changed use_advanced_ui to EditUI... Use this menu action to configure the plugins visible menu actions. Predefined
  settings are included, Simple, Advanced. (Advanced enables all actions)

#### 3/17/2015 ####
* updated install.sh. this should be the only required file to install pychron. this downloads/installs git,conda and pychron

#### 3/19/2015 ####
* added interpolation functionality to conditionals. For example "Ar40 < $MIN_INTENSITY". The value "MIN_INTENSITY" needs to be defined
  either in the options file or in the extraction scripts metadata. 

#### 3/25/2015 ####
* added ability to view source/deflection parameters for individual analyses

### Bug Fixes ###
* fixed plotting ideograms of attributes other than age
* improved database startup tests
* fixed plateau age calculation
* fixed spectrum label overlay. layout required when component's padding changes
* fixed spectrum log plotting

#### 2/3/2015 ####
* fixed spectrum legend. use aliquot if necessary to generate unique legend key
* fixed info overlay background rect. 
* fixed spectrum labels layout when spectrum changes

#### 2/4/2015 ####
* fixed isochron info placement
* fixed isochron atm indicator
* fixed updating isochron regression line
* fixed RectSelection/LimitsTools event collision
* fixed isochron autoscaling

#### 2/5/2015 ####
* updated x,y limits persistence

#### 2/7/2015 ####
* fixed AnalysisPointInspector for analysis number plots. was displaying uage... changed to Age
* fixed Plateau overlay placement. position 100px above nominal plateau or ymax-50px.

#### 2/10/2015 ####
* fixed diff editor. fixed age and rad yield diffing

#### 2/13/2015 ####
* fixed ErrorBarOverlay. trigger layout_needed when component changes
 
#### 3/18/2015 ####
*  fixed j transfer

### 4/17/2015 ####
* added settling_time option to switches/valves 



2.0.6
------------------
* added StartupTester. use setupfiles/startup_tests.yaml to configure
* added Next and Previous buttons to Recall
* added Select Same/Select Same Attribute... to Experiment Editor
* updated Dashboard and Labspy
* updated Email plugin
* updated Labnumber Entry
* refactored irradiation import. moved to standalone dialog
* changed spectrometer task to an EditorTask. 
* updated coincidence
* added transfer j from mass spec to pychron
* added toggle full window
* added detector intercalibration
* added UsersPlugin
* added extraction defaults to defaults.yaml
* added NotificationManager. a simple class for managing NotificationWidgets, modeless, always on top, 
 rounded message windows pinned to the upper right hand corner of a parent window
* improved ConditionalsView. Display active conditionals in a modal window if condition trips
* updated UpdatePlugin
* added ability to edit device configuration from Hardware task
* updated PreferencesDialog. Display categories in a TabularEditor instead of as Group tabs.
* added ReplicationTask for interacting with a replication db
* added predefined initializations
* added "Whats New" action. brings user to this doc.
* added Experiment Columns defaults. [root]/setupfiles/experiment_defaults.yaml
* fixed displaying irradiation holder
* added auto saving of experiment queues. Auto saves to a .bak file whenever values change or run added
* added SampleImageTask
* added notes to irradiation levels
* added task switching to Browser pane
* added Import Sample Data action. import samples from xls file.

### Bug Fixes###

#### 2/24/15 ####
* fixed step heat template editing

<!---
.. * fully implemented import irradiation from XLS file
.. * added ability to export irradiations from Pychron to MassSpec
-->


2.0.5 Released 11/2014
-----------------------
* added switching between blank histories
* added BlankDiffView
* started Workspace
* added switching between sample_view(Jake) and query_view(Al) in browser
* added "Time View" to sample table context menu. Use to display list of analyses based on
    date ranges defined by the selected labnumbers
* added project, irradiation enabled toggles
* if high or low post only filters defined load the analysis table with the date range
* added detector ic view
* added comment template
* use notebook for scan manager graphs
* updated Procedures. don't open multiple extraction line canvases
* added Find References context menu action
* added user login
* added ability to archive loads
* added identifier (Labnumber) top level filter
* added Filter/Results focus switching
* added group emailing
* gitified pyscripts
* added frequency template
* added LabBook Plugin
* added open boxes to spectrum
* added uncorrected ratios to Series
* unified conditionals editing
* added database version checking
* updated conditionals. can do and/or with multiple variables e.g Ar40>10 and age<10.0
* added wake command to ExtractionLinePyScript. jitters mouse to wake from screen saver
* added Edit Initialization action and view
* added Labeling to LabBook
* changed Pychrondata to Pychron. 
* added ability to set Pychron root directory in the preferences. Uses ~/Pychron as default
* moved use_login,multi_user from initialization file to preferences.

2.0.4
------------------
* implemented "overlap" concept for automated runs
* select existing users from db when writing an experiment
* record diode output (heat_power) and response (temp) for each analysis
* when diode enabled scan pyrometer and display colormapped indicator for temperature
* measure baselines between peak hops. can explicitly define a peak hop as a baseline.
* added context menu actions to Experiment Editor. Move to End, Move to Start, Move to ...
* APIS support
* updated Experiment estimated duration. 
* added Visual ExtractionLine Script programmer
* added Peak hop editor
* added context menu actions to UnknownsPane(unselect, group selected, clear grouping) and AnalysisTable(unselect, replace, append)
* added Open Additional Window action. use to open multiple windows of the same task type e.i two recall windows
* added Split Editor action
* updated grouping of unknowns. added auto_group toggle to UnknownsPane
* added date querying to top-level filtering in Browser
* updated frequency run addition
* added trough and rubberband patterns. modified stage map to accommodate rubberband pattern
* added graphical filtering to Browser
* added data reduction tagging
* added ability to configure recall view
* started permutator. use to generate all permutations of a dataset
* started summary views accessible for recall task
* added use_cdd_warming to experiment queue
* added preset decay constants for easy switching
* added default snapshot name (RunID_Pos) when used from pyscript, e.g. 12345-01A_3
* added note, last_modified to irrad_ProductionTable
* updated editing default_fits
* added snapshot view to recall
* added fontsize control to recall
* added task switching
* added time view to browser
* added ability to add event markers to spectrometer scan graph
* added snapshot to spectrometer scan
* added bgcolor control for experiment editor
* optimized plotpanel
* added "window" to AutomatedRunCondition. use to take a mean or std of "window" points
* added more options for AutomatedRunConditions
* added Queue/Default Conditionals
* updated user notification
* added procedures concept e.g. QuickAir
* added ImportIrradiationHolderAction
* added end_after and skip context menu actions
