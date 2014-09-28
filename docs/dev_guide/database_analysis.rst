IsotopeRecordView used for display in tables and fast creation and access.

IsotopeDatabaseManager.make_analyses(list_of_analyses) used to convert a
IsotopeRecordView to a DBAnalysis. make_analyses retrieves the analysis from the db
using a uuid. DBAnalysis is synced with the database record.

DBAnalysis is a subclass of ArArAge, Analysis.
loading the isotopes from the db is the costliest process.

View of the analysis is handled by an AnalysisView. each DBAnalysis has an analysis_view object.
the analysis is passed into analysis_view for creation.

AnalysisView is composed of multiple subview objects; MainView, HistoryView, ...
