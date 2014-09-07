CHANGELOG
============

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
* added snapshot view to recall. currently only a list of snapshots not the actual images
