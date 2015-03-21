=================
Remote Hardware
=================

Remote hardware is used to allow other software clients access to pychron hardware, such as valves and laser systems.
A simple messaging system is used to pass information between pychron and a client. Currently the most
active client is Mass Spec which uses the remote hardware protocol to do all of its hardware tasks. 

The protocol is broken in two sections :ref:`extraction_line_calls_label` and :ref:`laser_calls_label`.
Calls are simple ASCII text messages sent over the ethernet using either the `UDP <http://en.wikipedia.org/wiki/User_Datagram_Protocol>`_
or `TCP <http://en.wikipedia.org/wiki/Transmission_Control_Protocol>`_ internet protocols

A response to a call is ``OK``, a value, or an ErrorCode

.. toctree::
	el_errors
	laser_errors
	
.. _extraction_line_calls_label:

Extraction Line Calls
-------------------------

.. describe:: Open alias
	
	Open the valve called ``alias``. :ref:`InvalidValveErrorCode <invalid_valve_err>` return if ``alias`` not available

.. describe:: Close alias
	
	Close the valve called ``alias``. :ref:`InvalidValveErrorCode <invalid_valve_err>` return if ``alias`` not available

.. describe:: GetValveState alias

	Get ``alias`` state. Returns ``0`` for closed ``1`` for open

.. describe:: GetValveStates

	Get all the valves states as a word. Returns a string <alias><state> e.g. ``A1B0C1D1E0F0``

.. describe:: GetValveLockStates

	Get all the valves lock states as a word. Returns a string <alias><lock_state> e.g. ``A1B0C1D1E0F0``

.. describe:: StartMultRuns multruns_id

.. describe:: CompleteMultRuns

.. describe:: StartRun runid

.. describe:: CompleteRun

.. describe:: PychronScript script

.. describe:: ScriptState


.. _laser_calls_label:

Laser Calls
--------------

.. describe:: Enable

	Enable the laser.  This is required before the laser's power can be set using :ref:`SetLaserPower <set_laser_power>`
	
.. describe:: Disable

	Disable the laser

.. _set_laser_power:

.. describe:: SetLaserPower power
	
	Set the laser's power to ``power``. ``power`` must be between 0-100.  

.. describe:: ReadLaserPower

	Read the lasers internal power meter. Returns an 8 bit value i.e 0-255

.. describe:: GetLaserStatus

	Return OK if the laser can be enabled. If an interlock is enabled, such as insufficient coolant flow, an error will be returned
	
.. describe:: SetBeamDiameter

	Set the beam diameter setting. 

.. describe:: GetBeamDiameter
	
	Get the beam diameter setting. 
	
.. describe:: SetZoom zoom

	Set zoom. ``zoom`` must be between 0-100.  
	
.. describe:: GetZoom

	Get zoom. returns value between 0-100.
	
.. describe:: GetPosition
	
	Returns a comma separated list of positions X,Y,Z
	
.. describe:: GoToHole holenum

	Go to hole ``holename``. InvalidHoleErrorCode returned if hole is not in the current stage map.

.. describe:: GetJogProcedures

	Return a list of available Jog procedures. Jog is a MassSpec term and a misnomer. Pychron internal refers
	to them as Patterns.
	
.. describe:: DoJog name

	Launch the jog named ``name``.
	
.. describe:: AbortJog

	Abort the current jog
	
.. describe:: SetX xpos

	Set the laser's stage controller X axis to ``xpos``.
	
.. describe:: SetY ypos
	
	Set the laser's stage controller X axis to ``ypos``.

.. describe:: SetZ zpos
	
	Set the laser's stage controller X axis to ``zpos``.

.. describe:: SetXY xypos

	Set the laser's stage controller X and Y axes to ``xypos``. ``xypos`` should be a comma separated list of numbers.
	e.g ``SetXY 10.1,-5.03``
	
.. describe:: GetXMoving

.. describe:: GetYMoving

.. describe:: GetDriveMoving

.. describe:: StopDrive

.. describe:: SetDriveHome

.. describe:: SetHomeX

.. describe:: SetHomeY

.. describe:: SetHomeZ