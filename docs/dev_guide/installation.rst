Installation
============

Pychron now exposes a supported setup path through the CLI utilities in
``pychron/cli.py``.

Recommended workflow
--------------------

1. Create an environment with Python 3.12.
2. Install dependencies with ``uv sync`` and any profile-specific extras.
3. Bootstrap the runtime tree with ``pychron-bootstrap``.
4. Validate the result with ``pychron-doctor``.

Examples
--------

List the available generic profiles:

.. code-block:: bash

   pychron profiles --verbose

Print a supported install plan for a target machine:

.. code-block:: bash

   pychron install-plan --profile ngx --profile chromiumco2

Bootstrap a new installation:

.. code-block:: bash

   pychron-bootstrap --root ~/Pychron --profile data-reduction

Bootstrap using generic profiles plus external example bundles:

.. code-block:: bash

   pychron-bootstrap \
     --root ~/Pychron \
     --profile experiment \
     --source-profile felix \
     --setupfiles-source "/path/to/setupfiles" \
     --scripts-source "/path/to/scripts"

Validate an installation:

.. code-block:: bash

   pychron-doctor --root ~/Pychron --profile data-reduction

Export and import site configuration bundles:

.. code-block:: bash

   pychron export-config --root ~/Pychron --output ~/pychron-config.zip
   pychron import-config --root ~/Pychron_clone --archive ~/pychron-config.zip

Install extras
--------------

The project now exposes clearer optional dependency groups for hardware-oriented
installs:

- ``hardware``
- ``laser``
- ``spectrometer-ngx``
- ``valve``

These do not change the Pychron runtime path structure. They only make the
installation intent clearer when using ``uv sync --extra ...``.
