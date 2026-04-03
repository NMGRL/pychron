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

``pychron-bootstrap`` is the supported initialization and repair entrypoint.
The GUI first-run wizard and startup validation use the same bootstrap and
validation services, while preserving the existing runtime files such as
``setupfiles/initialization.xml`` and the ``preferences`` tree.

Examples
--------

List the available versioned starter bundles:

.. code-block:: bash

   pychron bundles --verbose

List the available generic profiles:

.. code-block:: bash

   pychron profiles --verbose

Print a supported install plan for a target machine:

.. code-block:: bash

   pychron install-plan --bundle ngx --bundle chromiumco2-lab

Bootstrap a new installation:

.. code-block:: bash

   pychron-bootstrap --root ~/Pychron --profile data-reduction

Repair an existing installation without overwriting site-authored files:

.. code-block:: bash

   pychron-bootstrap --root ~/Pychron --bundle ngx-collection

Bootstrap using a versioned starter bundle:

.. code-block:: bash

   pychron-bootstrap --root ~/Pychron --bundle ngx-collection

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
   pychron-doctor --root ~/Pychron --bundle ngx-collection --strict

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

Bootstrap-managed files include the default ``initialization.xml``,
``startup_tests.yaml``, and ``.appdata`` support files. Profile-specific files
with shipped defaults are also created when missing. Files without defaults are
still treated as lab-authored configuration and are reported by
``pychron-doctor`` with guidance instead of being silently overwritten.
