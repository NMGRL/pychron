RoadMap
----------------
 - Implement ratio calculation of ages
 - Implement offline workspace
 - ~~Deprecate RPC? move to one communication mechanism.~~
 - use zeromq for all sockets
 - Improve installation and cross-platform configuration UX
   - [x] add `pychron-doctor` environment and configuration diagnostics
   - [x] add `pychron-bootstrap` first-run setup/bootstrap command
   - [x] add a first-run setup wizard for GUI users
   - [x] ship versioned starter configuration bundles by workflow
   - [x] split dependencies into clearer install profiles/extras
   - [x] maintain supported installer/launcher paths per OS
   - [x] validate environment and config at startup with actionable errors
   - [x] support export/import of site configuration bundles
 - Improve pipeline and plotting responsiveness/maintainability
   - remove runtime debug prints from active pipeline/plotting code paths
   - normalize plot editor refresh/rebuild signaling
   - reduce unnecessary figure panel rebuilds
   - [x] centralize plot background/theme defaults
   - move demo/sandbox plotting code out of importable runtime modules
   - [x] tighten broad exception handling in plotting/refresh code
 - Improve NGX intensity acquisition reliability
   - refactor `NGXSpectrometer.read_intensities()` into explicit acquisition-state and parse helpers
   - validate `#EVENT:ACQ` / `#EVENT:ACQ.B` payloads before indexing or converting
   - replace fixed post-trigger sleeps with timeout-aware event waiting
   - separate command-response handling from acquisition event consumption
   - make NGX read timeouts scale with integration time
   - replace implicit detector ordering assumptions with explicit payload-to-detector mapping
   - add NGX-specific stale-acquisition detection based on event progression
   - remove legacy debug/locking leftovers from the NGX read path
   - add transcript-style tests for normal, malformed, timeout, and cancel cases
 - Improve experiment editor and executor coordination
   - centralize active editor/queue synchronization in the executor
   - make editor-driven queue mutations refresh stats/table/info immediately
   - consolidate queue-changed handling in the experiment factory
   - reduce stale selected-run/editor state when switching experiment tabs
   - add focused regression tests for executor/factory queue synchronization
 - Improve regression graph and regressor performance/reliability
   - avoid unnecessary regression recalculation when scatter data and exclusions are unchanged
   - avoid unconditional regression-graph relayout/redraw work on no-op updates
   - clear regressor dirty state deterministically after successful or failed fits
   - tighten broad exception handling in regression graph updates
   - add focused tests for regressor state reuse and dirty tracking
 - Improve analysis/isotope model and view responsiveness
   - reuse isotope regressors unless grouping/filter/fit state actually changes
   - stop rebuilding analysis view tabs and value tables unnecessarily
   - prevent repeated isotope-evolution grouping listeners from accumulating
   - replace broad exception/print handling in analysis view sync paths
   - add focused tests for main-view value reuse and isotope invalidation
 - Make experiment analysis execution state explicit
   - introduce an event-driven automated-run state machine
   - route collector/run/executor transitions through a shared transition API
   - record transition source/reason metadata for debugging and operator support
   - replace direct state mutation in queue validation/reset paths
   - add focused tests for event-driven transitions and transition metadata
 - Improve core reliability and maintenance hygiene
   - fix Python 3 persistence serialization/deserialization paths to use binary-safe I/O
   - replace Git host stdout error reporting with structured logging and actionable failures
   - remove remaining runtime debug prints from active regression/interpolation code paths
   - narrow broad exception handling in persistence and Git host runtime code
   - add focused regression coverage for persistence helpers where dependencies allow

v3.0.0
------------------
 - Pipeline
 - DVC
 
v2.1.0
------------------
 - major experiment versioon
 - first release used outside of NMGRL
 
v2.0.6
----------------
 - Improve labspy
 - irradiation/labnumber entry
 - Automated run monitor
 - auto mftable (Low priority)
 - add logger pane to Experiment, Spectrometer, ExtractionLine tasks.
 - add logger pane to AnalysisEdit tasks (?)
 - add analysis labnumber editing capabilities. See Issue \#480. 
   
v2.0.5
----------------
 - Conditionals Editing
 
 More testing
 - Whiff/Sniff
 - Labspy
 - LabBook
 - Gitified Directories
 - Run block editing
