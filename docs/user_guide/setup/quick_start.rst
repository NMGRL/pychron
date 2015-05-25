Quick Start (ish)
-----------------------------

Step 0. Downloads
==========================

    A. Download and install the excellent python IDE, PyCharm. A free community edition is available at https://www.jetbrains.com/pycharm/
    #. Install Git. https://git-scm.com/downloads
    #. Download the Anaconda Python Distribution from https://store.continuum.io/cshop/anaconda/. This download includes the Python standard library and numerous open
       source packages for science, engineering and application development. The excellent package manager ``conda`` is
       also included to install any additional dependencies
    #. Create an account at https://github.com. This free account will give you access to Pychron's source files, support files
       and even the source for this documentation.

    .. note:: For steps A-C you must open the downloaded package and run the installer.

Manual
===========================
    #. Create a directory called ``Pychron`` in your Home folder. ie ``/Users/<username>/Pychron`` where ``<username>`` is
       replaced with your user name, for the remainder of this documentation we will assume the username is ``argonlab``.
       This location will serve as the root directory for all Pychron configuration and data files.
    #. Create a directory called ``Programming`` in your Home folder. ``/Users/argonlab/Programming``
       This location will hold source files
    #. Open a terminal window. ``/Applications/Utilities/Terminal.app``
    #. Execute the following commands. These commands will move you to the ``Programming`` directory, then download the pychron
       source files into a directory called ``pychron``
       ::

         cd ~/Programming
         git clone https://github.com/<organization>/pychron.git

     .. note:: Replace ``<organization>`` with the name of your github organization. For example U. of Manitoba has its
               own pychron fork located at https://github.com/UManPychron/pychron.git
    5. Check to make sure you have the source files. You should see a number of files and subdirectories after executing
       the following commands
       ::

         cd ~/Programming/pychron
         ls

    #. Download the Pychron support files.
       ::

         cd ~/Programming
         git clone https://github.com/<organization>/support_pychron.git

    #. Move the directories in ``~/Programming/support_pychron`` to ``~/Pychron``
    #. Before you can launch Pychron you must install some dependencies.
       ::

         cd ~/Programming/pychron
         cd app_utils/requirements
         conda install --yes --file ./conda_requirements.txt
         pip install -r ./pip_requirements.txt

    # checkout the version of Pychron you want to use. The current release is v2.1.0
       ::

         cd ~/Programming/pychron
         git checkout release/v2.1.0

Auto (Beta)
===========================

.. warning:: This feature is experimental and should be used with caution.

use the installer script, install.sh or install_development.sh
