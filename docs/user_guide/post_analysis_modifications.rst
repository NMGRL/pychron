Post Analysis Modifications
=============================

Unfortunately it is not uncommon of an analysis to be collected and saved with in correct information.
For example the analysis by have been with a typo in the sample name or an incorrect sample name entirely.
Another example is the analysis is run with the wrong "identifier".


Fix Sample MetaData
----------------------
A sample's metadata is stored in the database. When an analysis of a sample is collected however, the sample
information is saved in the analysis json file. So simply changing the sample metadata will only affect future
analyses. In order to sync collected analyses with the database you need to use "Sync Repo/DB Sample Info" toolbar
action in the "Repositories" window. Select the repository that contains the analyses you want to update and click
"Sync Repo/DB Sample Info"


Fix Aliquot/Increment
-----------------------
Use Bulk Edit pipeline
