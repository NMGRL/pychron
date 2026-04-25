Pychron
=======

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3237834.svg)](https://doi.org/10.5281/zenodo.3237834)
[![Format code](https://github.com/PychronLabsLLC/pychron/actions/workflows/format_code.yml/badge.svg)](https://github.com/PychronLabsLLC/pychron/actions/workflows/format_code.yml)
[![CI](https://github.com/PychronLabsLLC/pychron/actions/workflows/ci.yml/badge.svg)](https://github.com/PychronLabsLLC/pychron/actions/workflows/ci.yml)

[Documentation](https://pychron.readthedocs.io/)
|
[Developer Guide](docs/dev_guide/index.rst)
|
[Change Log](CHANGELOG.md)
|
[Roadmap](ROADMAP.md)

Overview
========

Pychron is an open-source platform for noble gas mass spectrometry data acquisition, experiment control, and data reduction.
It is developed at the New Mexico Geochronology Research Laboratory at New Mexico Tech and is used primarily for Ar-Ar
geochronology and thermochronology workflows.

The codebase includes applications and subsystems for:

- automated experiment execution
- extraction line and laser control
- data reduction and plotting
- DVC-backed data and repository workflows
- mass spectrometer integration
- hardware communication and monitoring

Main Components
===============

``pyExperiment``
  Build and execute automated analysis queues.

``pyCrunch``
  Reduce, inspect, and export Ar-Ar data products.

``pyValve``
  Control and monitor extraction-line hardware.

``pyLaser``
  Operate supported laser systems and related motion/control hardware.

``furPi``
  Furnace-side control components for supported workflows.

Documentation
=============

Start with:

- [Project documentation](https://pychron.readthedocs.io/)
- [Developer guide](docs/dev_guide/index.rst)
- [Git workflow](docs/dev_guide/git_workflow.rst)
- [Repository settings](docs/dev_guide/repository_settings.rst)
- [Wiki install notes](https://github.com/NMGRL/pychron/wiki/Install)

Development
===========

The repo now uses GitHub Actions CI via [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

Setup utilities
===============

The repo now exposes a Typer-based CLI for basic setup and diagnostics:

- `pychron bundles --verbose`
- `pychron profiles --verbose`
- `pychron install-plan --bundle ngx --bundle chromiumco2-lab`
- `pychron-bootstrap --root ~/Pychron --profile data-reduction`
- `pychron-bootstrap --root ~/Pychron --bundle ngx-collection`
- `pychron-bootstrap --root ~/Pychron --profile ngx --profile chromiumco2`
- `pychron-bootstrap --root ~/Pychron --profile experiment --source-profile felix --setupfiles-source "<setupfiles-dir>" --scripts-source "<scripts-dir>"`
- `pychron-doctor --root ~/Pychron --profile data-reduction`
- `pychron-doctor --root ~/Pychron --bundle ngx-collection --strict`
- `pychron export-config --root ~/Pychron --output ~/pychron-config.zip`
- `pychron import-config --root ~/Pychron_clone --archive ~/pychron-config.zip`
- `python -m pychron doctor`

The CLI bootstrap path is the canonical initialization flow. The GUI first-run
wizard and startup validation now use the same runtime bootstrap and validation
services, so operator-facing setup and repair behavior stays aligned.

Typical workflow:

1. Branch from `develop` or the active integration branch.
2. Make focused changes on a short-lived `codex/*` or `feature/*` branch.
3. Run targeted tests locally when possible.
4. Open a PR into the branch you started from.

See [the developer workflow guide](docs/dev_guide/git_workflow.rst) for the branch model and release process.

Who Uses Pychron
================

Pychron and related tooling are used by multiple Ar/Ar geochronology and noble gas laboratories, including:

- New Mexico Geochronology Research Laboratory
- University of Manitoba
- WiscAr, University of Wisconsin
- USGS Denver
- Lamont-Doherty Earth Observatory
- USGS Menlo Park
- NASA Goddard Space Flight Center
- University of Arizona

Citation
========

If Pychron contributed to published data collection or data reduction, cite the current release or DOI record when possible.
One commonly referenced citation is:

Jake Ross. (2019). NMGRL/pychron v18.2. Zenodo. https://doi.org/10.5281/zenodo.3237834
