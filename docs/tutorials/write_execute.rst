Writing and Executing Experiments
==================================

.. _writing-exp-queues-label:

Writing Experiment Queues
------------------------------

#.  Make a New experiment...
    
    .. image:: ../images/tutorial/new_exp_queue_menu.png
        :scale: 100%    
    
#.  Or Open an existing experiment queue.
    
    .. image:: ../images/tutorial/open_exp_queue_menu.png
        :scale: 100%

    .. image:: ../images/tutorial/exp_editor.png
        :scale: 100%
   
#.  Set the ``Mass Spectrometer``.
#.  Set the ``Extract Device``.
#.  Set ``Delay before Analyses``.
#.  Set ``Delay between Analyses``.
#.  (Optional) Set the ``Tray``. (As of 4/12/13 not fully implemented)
#.  Enter a ``Labnumber``.

    A.  type in a Labnumber ``e.g 23412 or bg``.
    #.  choose from drop-down.
    #.  choose from Special Labnumber drop-down. 
    
#.  For unknowns set ``Extract Value`` and ``Extract Units``.
#.  For unknowns and blanks set ``Duration``. Duration is the amount of time to do the extraction. 
    For the CO2 laser this corresponds to the total lasing time. For the UV laser in burst mode 
    duration corresponds to the amount of time (s) to complete ``N`` bursts at the current ``Reprate``.
#.  Set ``Cleanup``. Set the amount of time in seconds to getter the sample gas. 
    Note unlike Mass Spec ``Duration`` is not considered part of the cleanup- ``Duration`` 
    and ``Cleanup`` are executed consecutively. In Mass Spec one might set ``FirstStageDelay=180`` 
    and ``Duration=30``. The pychron equivalent is ``Duration=30``, ``Cleanup=150``. However, this behavior is 
    entirely dictated by how one writes the Extraction script, therefore different behaviors are readily achievable.
#.  Modify the scripts. Defaults scripts are determined based on the extraction device and labnumber. Defaults are defined at ``~/Pychrondata_<version>/scripts/defaults.yaml``
#.  Hit Add


   
Executing Experiments
----------------------

#.  Write a new experiment. See :ref:`writing-exp-queues-label`
#.  Or execute an existing experiment.

    .. image:: ../images/tutorial/exc_exp_queue_menu.png
        :scale: 100%
        
    .. image:: ../images/tutorial/exp_executor.png
        :scale: 100%
        
#.  Hit Start (#4)