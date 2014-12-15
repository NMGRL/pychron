Installer
=============

.. _make-app-bundle:

Build Pychron as a Mac OSX application 
---------------------------------------

#.  Open Terminal and cd to parent directory of the source you want to build.
    
    ::
    
        ross$ cd path/to/src/parent
     
#.  Run installer_script.py. (Replace <version> with the name of the pychron flavor you want to build. e.g experiment for pyexperiment. 
    
    ::
    
        ross$ python pychron_<version>/src/apptools/install_script.py -a -Apychron_<version> pychron_<version>/
    
    installer_script.py help
    
    ::
        
        ross$ python pychron_experiment/src/apptools/install_script.py -h
        usage: install_script.py [-h] [-d] [-f] [-a] [-s] [-v VERSION] [-A APPLICATIONS] [-r ROOT] N

        Install Pychron
        
        positional arguments:
          N                     name of the cloned source directory
        
        optional arguments:
          -h, --help            show this help message and exit
          -d, --data            overwrite the current pychron_data directory
          -f, --force-data      dont ask to overwrite the data dir, just do it
          -a, --apps-only       only create the app bundles
          -s, --source          download source
          -v VERSION, --version VERSION
                                set the version number e.g 1.0
          -A APPLICATIONS, --applications APPLICATIONS
                                set applications to build e.g pychron_experiment
          -r ROOT, --root ROOT  set the root directory

#.  Typical output if successful.
    
    ::
    
        Using . as working dir
        experiment
        
        Building pychron.py as pyexperiment.app
        ./pychron_experiment/launchers/pychron.py
        ./pychron_experiment/resources/apps/pyexperiment_icon.icns
        Copying entire src tree
        Copying include_mods...
        Created ./pychron_experiment/launchers/pychron.py
        renaming pychron to pyexperiment