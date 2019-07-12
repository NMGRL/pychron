Ratio Change Detection
------------------------

Ratio Change Detection are enabled ``Preferences/Experiment`` and configured using 
``setupfiles/ratio_change_detection.yaml``

```yaml
- ratio: Ar40/Ar36
  nanalyses: 5
  threshold: 1
  percent_threshold: 1
  nominal_ratio: 295
  nsigma: 3 
  analysis_type: air
  failure_count: 2
  consecutive_failure: True
- ratio: Ar40/Ar39
  nanalyses: 5
  threshold: 1
  percent_threshold: 1
  nominal_ratio: 10
  nsigma: 3
  analysis_type: cocktail
  failure_count: 2
  consecutive_failure: True
```