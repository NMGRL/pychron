# Data Reduction

## Purpose

Describe the path from stored analyses to reduced results, figures, tables, and exports. In current Pychron this mostly means DVC-backed retrieval plus pipeline-node execution and processing models.

## Main modules

- `pychron/dvc/`: analysis retrieval, repository access, metadata, and persistence services
- `pychron/pipeline/engine.py`: pipeline orchestration
- `pychron/pipeline/nodes/`: composable reduction, plotting, review, and persistence steps
- `pychron/pipeline/tasks/`: Pipeline task/plugin wiring
- `pychron/pipeline/plot/editors/`: figure editors
- `pychron/processing/`: reduction models, grouping, Ar-Ar calculations, and derived results

## Key classes

- `DVC`
- `DVCPersister`
- `PipelinePlugin`
- `PipelineTask`
- `PipelineEngine`
- `Pipeline`
- `BaseNode`
- `IdeogramNode`, `SpectrumNode`, `SeriesNode`
- `DVCAnalysis`
- `AnalysisGroup`

## Dependency boundaries

- `DVC` owns repository/database access; pipeline nodes should request data through that layer rather than reimplement persistence logic.
- `PipelineEngine` and `Pipeline` coordinate node execution; individual nodes should stay focused on one transformation or output step.
- Plot editors and processing models should consume reduced data products, not perform ad hoc repository access from UI code.
- Numerical reduction logic belongs in `pychron/processing`, while workflow assembly belongs in `pychron/pipeline`.

## Common extension points

- Add new reduction or export workflows by creating a node under `pychron/pipeline/nodes/` and registering it in the pipeline task flow.
- Add new default pipelines and templates through pipeline defaults and template support.
- Add new figure or review experiences by extending the plot editors and figure nodes.
- Extend repository-backed behavior through `DVC`, `DVCPersister`, or repo task integrations.

## Known sharp edges

- Data reduction mixes UI state, cached analyses, DVC repository state, and processing models; stale-data issues are common.
- Pipeline nodes often assume prior nodes populated specific parts of `EngineState`; reordering nodes can break flows indirectly.
- The same analyses may be represented as DVC models, processing models, and plotted records at different stages, so type confusion is easy.
- Some workflows depend on local repositories and external metadata being present; failures may look like plotting bugs when the real issue is missing DVC state.
