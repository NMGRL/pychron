Startup Tests
-------------

Startup tests are enabled using ``setupfiles/startup_tests.yaml``

```yaml
- plugin: DatabasePlugin
  tests:
    - test_pychron
    - test_pychron_version
- plugin: MassSpecPlugin
  tests:
    - test_database
- plugin: LabBookPlugin
  tests:
- plugin: ArArConstantsPlugin
  tests:
- plugin: ArgusSpectrometerPlugin
  tests:
    - test_communication
    - test_intensity
- plugin: ExtractionLinePlugin
  tests:
    - test_valve_communication
    - test_gauge_communication
- plugin: DVC 
  tests:
    - test_database
    - test_dvc_fetch_meta
- plugin: GitHub
  tests:
    - test_api
    
- plugin: NMGRLFurnacePlugin
  tests:
    - test_furnace_api
    - test_furnace_cam
```