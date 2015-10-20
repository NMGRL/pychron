=======================
General
=======================

.. code-block:: python

	#==========================================================
	def main():
	    info('this is an info message')
	    acquire('pipette')
	    info('aquired resourece - pipette')
	    sleep(15)
	    release('pipette')
	    begin_interval(120)
	    #do some stuff ...
	    complete_interval() #wait until 120 seconds have passed
	#===============================================================		
	    
--------------------------
functions
--------------------------

.. py:function:: info(msg)
	
	add info ``msg`` to the log

.. py:function:: acquire(resource)
	
	reserve the :py:attr:`resource` for use. blocks other scripts from using :py:attr:`resource` until
	:py:func:`release` is called.

.. py:function:: release(resource)

	release :py:attr:`resource` so other scripts can use it.
	
.. py:function:: sleep(seconds)

	sleep for :py:attr:`seconds`. if ``seconds>5`` a timer will appear. decimal seconds are allowed e.g ``sleep(0.5)``
	   
.. py:function:: gosub(path_to_script)
	
	execute a pyscript located at :py:attr:`path_to_script`. :py:attr:`path_to_script` is relative to the current 
	script. e.g ``gosub(commonscripts/fuse.py)``. ``commonscripts`` must be a directory in the same 
	directory this script is saved in.
	
.. py:function:: begin_interval(timeout)
	
	start an interval. if ``timeout>5`` a timer will appear. 
	
.. py:function:: complete_interval()

	wait unit :py:attr:`timeout` has elapsed