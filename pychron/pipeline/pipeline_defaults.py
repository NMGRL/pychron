# ===============================================================================
# Copyright 2018 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
ML = """
required:
nodes:
  - klass: MLDataNode
  - klass: MLRegressionNode
"""

REGRESSION_SERIES = """
required:
nodes:
  - klass: UnknownNode
  - klass: RegressionSeriesNode
"""
RADIAL = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: RadialNode
"""
YIELD = """
required:
nodes:
  - klass: UnknownNode
  - klass: YieldNode
"""

ICFACTOR = """
required:
nodes:
  - klass: UnknownNode
  - klass: FindReferencesNode
    threshold: 10
    analysis_types: 
      - Air
    name: Find Airs
  - klass: ReferenceNode
  - klass: FitICFactorNode
  - klass: ReviewNode
  - klass: ICFactorPersistNode
"""

DEFINE_EQUILIBRATION = """
required:
nodes:
  - klass: UnknownNode
  - klass: DefineEquilibrationNode
  - klass: ReviewNode
  - klass: DefineEquilibrationPersistNode
    use_editor: False
"""

ISOEVO = """
required:
nodes:
  - klass: UnknownNode
  - klass: FitIsotopeEvolutionNode
  - klass: ReviewNode
  - klass: IsotopeEvolutionPersistNode
    use_editor: False
"""

BLANKS = """
required:
nodes:
  - klass: UnknownNode
  - klass: FindBlanksNode
    threshold: 10
    name: Find Blanks
  - klass: ReferenceNode
  - klass: FitBlanksNode
  - klass: ReviewNode
  - klass: BlanksPersistNode
"""

CSV_IDEO = """
required:
nodes:
  - klass: CSVNode
  - klass: IdeogramNode
"""

IDEO = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: IdeogramNode
"""

INVERSE_ISOCHRON = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: InverseIsochronNode
"""

SPEC = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: SpectrumNode
"""

COMPOSITE = """
required:
nodes:
  - klass: UnknownNode
  - klass: CompositeNode
"""

FLUX_VISUALIZATION = """
required:
nodes:
  - klass: FindFluxMonitorMeansNode
    # level: K
    # irradiation: NM-300
  - klass: FluxVisualizationNode
"""

VERTICAL_FLUX = """
required:
nodes:
  - klass: FindVerticalFluxNode
  - klass: VerticalFluxNode
"""

XY_SCATTER = """
required:
nodes:
  - klass: UnknownNode
  - klass: XYScatterNode
"""

ANALYSIS_TABLE = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: SubGroupingNode
  - klass: AnalysisTableNode
  - klass: ReviewNode
  - klass: XLSXAnalysisTablePersistNode
"""

ANALYSIS_TABLE_W_IA = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: SubGroupingNode
  - klass: AnalysisTableNode
  - klass: ReviewNode
  - klass: SetInterpretedAgeNode
  - klass: ReviewNode
  - klass: InterpretedAgePersistNode
  - klass: XLSXAnalysisTablePersistNode
  
"""

INTERPRETED_AGE_TABLE = """
required:
nodes:
  - klass: InterpretedAgeNode
  - klass: InterpretedAgeTableNode
  - klass: ReviewNode
  - klass: InterpretedAgeTablePersistNode
"""

INTERPRETED_AGE_IDEOGRAM = """
required:
nodes:
  - klass: InterpretedAgeNode
  - klass: IdeogramNode
"""

HYBRID_IDEOGRAM = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: InterpretedAgeNode
  - klass: IdeogramNode
"""

SUBGROUP_IDEOGRAM = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: SubGroupingNode
  - klass: GroupAgeNode
  - klass: ReviewNode
  - klass: IdeogramNode
"""

HISTORY_IDEOGRAM = """
required:
nodes:
  - klass: UnknownNode
  - klass: DVCHistoryNode
  - klass: HistoryIdeogramNode
"""

HISTORY_SPECTRUM = """
required:
nodes:
  - klass: UnknownNode
  - klass: DVCHistoryNode
  - klass: SpectrumNode
"""

REPORT = """
required:
nodes:
  - klass: UnknownNode
  - klass: ReportNode
"""

SERIES = """
required:
nodes:
  - klass: UnknownNode
  - klass: SeriesNode
"""

FLUX = """
required:
nodes:
  - klass: FindFluxMonitorsNode
    # irradiation: NM-299
    # level: A
  - klass: FluxMonitorsNode
  - klass: FitFluxNode
  - klass: ReviewNode
  - klass: FluxPersistNode
"""

CSV_ANALYSES_EXPORT = """
required:
nodes:
  - klass: UnknownNode
  - klass: CSVAnalysesExportNode
"""

CSV_RAW_DATA_EXPORT = """
required:
nodes:
  - klass: UnknownNode
  - klass: CSVRawDataExportNode
"""

CA_CORRECTION_FACTORS = """
required:
nodes:
  - klass: UnknownNode
  - klass: CaCorrectionFactorsNode

"""

K_CORRECTION_FACTORS = """
required:
nodes:
  - klass: UnknownNode
  - klass: KCorrectionFactorsNode

"""

ANALYSIS_METADATA = """
required:
nodes:
  - klass: UnknownNode
  - klass: AnalysisMetadataNode

"""

BULK_EDIT = """
required:
nodes:
  - klass: UnknownNode
  - klass: BulkEditNode"""

AUDIT = """
required:
nodes:
  - klass: UnknownNode
  - klass: AuditNode
"""

MASSSPEC_REDUCED = """
required:
nodes:
  - klass: UnknownNode
  - klass: MassSpecReducedNode
"""

# ============= EOF =============================================
