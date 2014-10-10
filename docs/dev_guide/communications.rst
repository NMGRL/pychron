Communications
====================


Pychron/Pychron Communication
------------------------------

.. code-block:: python

   |====PyExperiment=====|
   | PychronLaserManager |
   |         |           |
   |    communicator     |
   |         |           |        |=====================================================|
   |         v           |        ||=RemoteHardwareManager=|                            |
   |        ask ---------|--LAN-->|| RemoteHardwareServer  |                            |
   |         ^-----------|--------||       ^   |           |                            |
   |=====================|        ||       |   v           |                            |
                                  ||      handler          |                            |
                                  ||       ^   |           |                            |
                                  ||       |   v           |        |=PyLaser/PyValve==||
                                  ||   CommandRepeater ----|--IPC-->| CommandProcessor ||
                                  ||       ^---------------|--------|     ^   |        ||
                                  ||=======================|        |     |   v        ||
                                  |                                 |    handler       ||
                                  |                                 |     ^   |        ||
                                  |                                 |     |   v        ||
                                  |                                 |    Manager       ||
                                  |                                 |==================||
                                  |                                                     |
                                  |=====================================================|


Pychron/Qtegra Communications
--------------------------------

.. code-block:: python

   |====PyExperiment=====|
   | ArgusSpectrometer   |
   |         |           |
   |   microcontroller   |
   |         |           |
   |    communicator     |
   |         |           |
   |         v           |        |=======Qtegra=========|
   |        ask ---------|--LAN-->| RemoteControlServer  |
   |         ^-----------|--------|       ^   |          |
   |=====================|        |       |   v          |
                                  |   ParseAndExecute    |
                                  |======================|