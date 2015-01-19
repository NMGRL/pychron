Experiment Construction
=============================

.. code-block:: python

    Class(name)

    ExperimentEditorTask->Experimentor(manager)

    Experimentor->ExperimentExecutor(executor)
                ->ExperimentFactory->QueueFactory(queue_factory)
                                   ->AutomatedRunFactory(run_factory)->FactoryView(factory_view)

    ExperimentEditor->ExperimentQueue(queue)->List(executed_runs)
                                            ->List(automated_runs)


    ExperimentFactoryPane -- QueueFactory, AutomatedRunFactory, FactoryView


New
----------------


Open
----------------


What Happens when Add Fired
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

      _add_button_fired
               |
        add_consumable


        ConsumerMixin
               |
           _add_run
               |
      AutomatedRunFactory
               |
            new_runs => runs, freq
                             |
                   ExperimentQueue
                     |
                   add_runs
                     |
                   automated_runs.extend(runs)