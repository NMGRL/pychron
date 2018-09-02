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
GEOCHRON = """
required:
 - pychron.geochron.geochron_service.GeochronService
nodes:
 - klass: UnknownNode
 - klass: GeochronNode
"""
ICFACTOR = """
required:
nodes:
  - klass: UnknownNode
  - klass: FindReferencesNode
    threshold: 10
    analysis_types: 
      - Air
  - klass: ReferenceNode
  - klass: FitICFactorNode
    fits:
      - numerator: H1
        denominator: CDD
        standard_ratio: 295.5
        analysis_type: Air
        save_enabled: True
        plot_enabled: True
  - klass: ReviewNode
  - klass: ICFactorPersistNode
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
  - klass: InverseIsochronNode
"""

SPEC = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: SpectrumNode
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

AUTO_IDEOGRAM = """
required:
nodes:
  - klass: ListenUnknownNode
  - klass: FilterNode
    filters:
     - age>0
  - klass: GroupingNode
    key: Identifier
  - klass: IdeogramNode
    no_analyses_warning: False
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

AUTO_REPORT = """
required:
nodes:
  - klass: CalendarUnknownNode 
  - klass: ReportNode
  - klass: EmailNode
"""
AUTO_SERIES = """
required:
nodes:
  - klass: ListenUnknownNode
  - klass: SeriesNode
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
#  irradiation: NM-274
#  level: E
  - klass: FluxMonitorsNode
#  - klass: GroupingNode
#  key: Identifier
#  - klass: IdeogramNode
#  - klass: TableNode
#  - klass: ReviewNode
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

CORRECTION_FACTORS = """
required:
nodes:
  - klass: UnknownNode
  - klass: CorrectionFactorsNode

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
