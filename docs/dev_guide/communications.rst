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


Description
---------------------------------
RemoteCommandServer is a top level object that doesnt do much.
TCPServer is a subclass of SocketServer.ThreadingTCPServer
TCPServer doesnt do much either. MessagingHandler is where the real work
happens.

The TCPServer listens for incoming commands and creates a new MessageHandler object for each
request ie command and calls its handle function

The handler object gets the data from the socket, processes it, and returns the result

To process requests the command is repeated using the CommandRepeater to the CommandProcessor
living in Pychron

The CommandRepeater prepends a process_type string to the beginning of the request so the
RemoteHardwareManager knows how to handle the request. The process_type and data are
separated by a pipe character ex. 'System|Open V'

CommandProcessor is a simple socket server, (NOTE: isnt a subclass of a SocketServer, uses a
listener thread to wait for requests from CommandRepeater)

When CommandProcessor receives a request its passed to
RemoteHardwareManager.process_server_request


------------------------------RemoteHardwareServer------------------------------------
--------------------------------------------------------------------------------------
TCPServer --> MessagingHandler.handle --> CommandRepeater.get_response -->
--------------------------------------------------------------------------------------

-------------------------------------Pychron------------------------------------------
--------------------------------------------------------------------------------------
CommandProcessor._handler --> RemoteHardwareManager.process_server_request -->

[Request_type]Handler.handle --> result
--------------------------------------------------------------------------------------

return result up the call stack
