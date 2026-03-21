GitHub Repository Settings
==========================

These settings are the recommended baseline for this repository.


Protected Branches
------------------

Protect these branch patterns:

* ``develop``
* ``main``
* ``dev/*``
* ``release/*``
* ``hotfix/*``

Recommended protections:

* require a pull request before merging
* require approval from at least 1 reviewer
* require conversation resolution before merge
* require status checks to pass before merge
* require branches to be up to date before merge
* dismiss stale approvals when new commits are pushed
* restrict direct pushes to administrators only when necessary


Required Status Checks
----------------------

At minimum require:

* ``Black``
* ``Unit Tests``

If CI expands later, keep the required list short and stable. Only require
checks that are reliable enough to gate merges consistently.


Merge Settings
--------------

Recommended:

* enable squash merge
* enable rebase merge only if the team actively prefers it
* disable merge commits unless preserving branch topology is important
* enable automatic deletion of head branches after merge


Pull Request Expectations
-------------------------

Each PR should include:

* a short summary of the change
* the reason for the change
* test or verification notes
* any known risks, follow-ups, or rollout notes


Branch Targeting
----------------

Use the same target branch you branched from:

* feature work from ``develop`` returns to ``develop``
* stream-specific work from ``dev/<stream>`` returns to that ``dev/<stream>``
* release stabilization returns to ``release/*``
* urgent fixes return to the deployed branch first, then back-port to
  ``develop``


Review Guidance
---------------

Require extra care for changes touching:

* experiment execution
* automated runs
* PyScript execution and context
* hardware communication
* database or DVC persistence

For those areas, prefer:

* smaller PRs
* explicit test notes
* reviewer attention on behavior and regression risk, not only style

