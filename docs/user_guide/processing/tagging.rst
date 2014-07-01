Tagging
---------

There are two types if tagging in Pychron

    1. `Analysis Tagging`_
    2. `Data Reduction Tagging`_


Analysis Tagging
~~~~~~~~~~~~~~~~
Analysis tagging is used to tag individual analyses and specify how pychron should handle the analysis when processing and plotting.
There are two generic tags, **OK** and **Invalid**. **OK** is the default tag for an analysis. It indicates that the analysis is acceptable a should be included in
all processes. **Invalid** indicates that the analysis is *bad* and should not be hidden from the browser and plotting routines

.. note:: The **Browser** includes a checkbox to include **Invalid** analyses in the results. By default this it is set to False

In addition to the two generic tags, users have to option to create there own tags. This user defined tags can have any name and also come with four options for
handling the plotting behavior. These options are

    1. `omit_ideo`
    2. `omit_spec`
    3. `omit_iso`
    4. `omit_series`

These options indicate whether the analysis should be excluded from the plot. Excluded in this context does not mean *not visible*, rather the analysis is
given a special marker indicating it is not used in the calculations. For example omitted analyses in an ideogram are displayed as red open squares and are not
used in the calculation of the mean age.

To add an analysis tag to one or more analyses

    1. Select a set of analyses using one of the following steps
        a. select analyses from browser
        b. select analyses from Unknowns
        c. graphically select analyses on figure
    2. Go to `Data/Tag`
    3. Select existing tag or make a new one
    4. (optional) fine-tune analysis select
    5. Click `OK` to apply of `Cancel` to cancel


Data Reduction Tagging
~~~~~~~~~~~~~~~~~~~~~~

Data reduction tagging is used to preserve the state of a set of analyses. This slightly analogous to the branching data model used in software development, namely Git.
For example, say you would like to reduce a set of data with all parabolic fits and then compare it to all linear fits. Data reduction tagging allows the user
to save each data reduction session, one for parabolic fits and one for linear, and easily toggle between the two sets.

To add a data reduction tag

    1. Perform the desire data reduction
    2. Selected a set of analyses in the browser
    3. Go to `Data/Data Reduction Tag`
    4. Give the tag a name
    5. Click `OK` to apply of `Cancel` to cancel

To toggle between data reduction tags

    1. Go to `Data/Set Data Reduction Tag`
    2. Select the desired tag from the table. You can filter by tag name and/or user
    3. Click `OK` to apply of `Cancel` to cancel

.. note:: If you select a set of analyses prior to step 1. pychron will only display the data reduction tags which contain the selected set of analyses
