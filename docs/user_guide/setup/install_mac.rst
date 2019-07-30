Mac Installer Script
=====================
Installation steps

1. :ref:`Setup Github Account`
2. :ref:`Download and Install Git`
3. :ref:`Download and Install Anaconda3`
4. :ref:`Download and Run installer`
5. :ref:`Setup Environment`
6. :ref:`Setup Plugins`
7. :ref:`Setup Preferences`


Setup Github Account
----------------------
    1. Go to github.com and create an account
    2. Setup a `Personal Access Token <https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line>`_
        a. Sign in to your account
        b. Go to your Settings ``github.com/settings/profile``
        c. Go to "Developer settings" ``github.com/settings/apps``
        d. Go to "Personal access tokens" ``github.com/settings/tokens``
        e. Generate new token, make sure "repo" is selected in "Select scopes"
        f. Copy the token for use when `Setup Preferences`_


Download and Install Git
-----------------------------

https://git-scm.com/downloads


Download and Install Anaconda3
----------------------------------

https://www.anaconda.com/distribution/


Download and Run installer
----------------------------

use ``Terminal.app`` or equivalent

.. code-block:: bash

    $ wget https://raw.githubusercontent.com/NMGRL/pychron/develop/app_utils/install.py

or

.. code-block:: bash

    $ curl -O https://raw.githubusercontent.com/NMGRL/pychron/develop/app_utils/install.py

run the script from the terminal

.. code-block:: bash

    $ cd /path/to/install.py
    $ python install.py


Setup Environment
---------------------
Launch Pychron and select your Pychron environment directory, typically ``/Users/<username>/Pychron`` or
``/Users/<username>/Pychron3``


Setup Plugins
---------------

The following plugins are the minimum requirements for data reduction. Additional plugins may be necessary or desired
for enhanced functionality. Enabled/Disable Plugins by manually editing the ``initialization.xml`` file or
``MenuBar/Help/Edit Initialization``

    - DVC
    - GitHub
    - Pipeline
    - ArArConstants


Setup Preferences
-------------------

Launch Pychron and go to ``Pychron/Preferences``

1. Go to ``Preferences/GitHub`` and enter in the Personal access token generated in :ref:`Setup Github Account`
2. Go to ``Preferences/DVC`` and setup a database connection

