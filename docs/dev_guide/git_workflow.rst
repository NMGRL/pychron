Git Workflow
============

Goals
-----

Pychron needs a workflow that supports:

* steady integration work on ``develop``
* occasional long-lived development streams such as ``dev/*``
* release stabilization without blocking normal development
* urgent fixes for deployed versions

This workflow is intentionally simpler than classic GitFlow. ``develop`` is the
main integration branch.


Branch Types
------------

``develop``
  Primary integration branch. Most work should merge here first.

``dev/<stream>``
  Optional long-lived team or subsystem branch. Use only when a stream needs to
  remain isolated for multiple weeks or when integration risk is high.

``codex/<topic>`` or ``feature/<topic>``
  Short-lived working branches for a single feature, fix, refactor, or cleanup.

``release/<version-or-name>``
  Stabilization branches created from ``develop`` when preparing a release.

``hotfix/<topic>``
  Urgent fixes created from the currently deployed release branch, or from
  ``main`` if ``main`` is the production source of truth.


Default Development Flow
------------------------

1. Branch from the correct base.

   * Use ``develop`` for normal work.
   * Use the active ``dev/*`` branch only if the work is explicitly tied to
     that stream.

2. Keep the branch small and focused.

   * One subsystem or one coherent change per branch.
   * Prefer multiple small PRs over one large mixed PR.

3. Open a pull request back to the branch you started from.

   * ``feature/...`` from ``develop`` goes back to ``develop``.
   * ``codex/...`` from ``dev/dc2025`` goes back to ``dev/dc2025``.

4. Keep the branch current.

   * Rebase on the target branch when practical.
   * Merge from target only when rebasing is unsafe or too disruptive.

5. Merge only when CI passes and review is complete.


When To Use ``dev/*`` Branches
------------------------------

``dev/*`` branches are useful when:

* a multi-week subsystem effort would destabilize ``develop``
* a deployment stream has different timing than the rest of the repo
* a hardware-specific or customer-specific stream must be isolated temporarily

``dev/*`` branches are not the default for ordinary work. Prefer short-lived
feature branches unless the stream genuinely needs to persist.


Release Flow
------------

1. Merge completed work into ``develop``.
2. Cut ``release/<version>`` from ``develop``.
3. Allow only stabilization work on the release branch:

   * bug fixes
   * documentation updates
   * version changes
   * release notes

4. Tag the release from the release branch.
5. Merge the final release state into ``main`` if ``main`` is used to represent
   shipped code.
6. Merge release fixes back into ``develop``.


Hotfix Flow
-----------

1. Branch ``hotfix/<topic>`` from the deployed branch.
2. Make the smallest possible fix.
3. Open a PR to the deployed branch.
4. After merge, back-merge or cherry-pick the fix into ``develop``.


Commit and PR Conventions
-------------------------

Use short, subsystem-prefixed commit and PR titles. Examples:

* ``experiment: centralize queue metadata propagation``
* ``pyscript: fail validation when a configured script is missing``
* ``graph: replace runtime prints with logging``

Recommended commit behavior:

* commit frequently while working
* squash merge by default for cleanup branches
* preserve individual commits only when commit history adds debugging value


Rules
-----

* Do not push directly to ``develop``, ``main``, ``release/*``, or shared
  ``dev/*`` branches.
* All shared-branch changes go through pull requests.
* CI must pass before merge.
* At least one reviewer is required for normal work.
* At least two reviewers are recommended for risky areas such as:

  * experiment execution
  * hardware communication
  * DVC persistence
  * automated run / pyscript integration


Recommended Branch Naming
-------------------------

* ``codex/qt-import-cleanup``
* ``codex/experiment-queue-metadata``
* ``feature/pyscript-fallback-resolution``
* ``hotfix/queue-parser-null-script``
* ``release/2026.3.0``


Current Repo Recommendation
---------------------------

For this repository:

* treat ``develop`` as the main trunk
* keep ``dev/*`` only for true long-lived streams
* use short-lived ``codex/*`` or ``feature/*`` branches for normal work
* require PRs and CI for all merges into shared branches

