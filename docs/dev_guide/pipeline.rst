Pipeline
=================


Structure
---------------
PipelinePlugin
     |
PipelineTask
     |
PipelineEngine
     |
  Pipeline
     |
   Nodes



Nodes
-----------------

Data
**************
UnknownNode, ReferenceNode, FluxMonitorsNode, ListenUnknownNode, CSVNode, InterpretedAgeNode

Diff
**************
from pychron.pipeline.nodes.diff import DiffNode

Figure
**************
IdeogramNode, SpectrumNode, SeriesNode, InverseIsochronNode, VerticalFluxNode

Filter
**************
FilterNode

Find
**************
FindReferencesNode, FindFluxMonitorsNode, FindVerticalFluxNode

Fit
**************
FitIsotopeEvolutionNode, FitBlanksNode, FitICFactorNode, FitFluxNode

Gain
**************
GainCalibrationNode

Grouping
**************
GroupingNode

Persist
**************
DVCPersistNode, PDFFigureNode, BlanksPersistNode, IsotopeEvolutionPersistNode, ICFactorPersistNode, FluxPersistNode,
XLSTablePersistNode, InterpretedAgeTablePersistNode

Review
**************
ReviewNode

Table
**************
AnalysisTableNode, InterpretedAgeTableNode
