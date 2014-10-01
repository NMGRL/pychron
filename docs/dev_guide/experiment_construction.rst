ExperimentConstruction
=============================
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
