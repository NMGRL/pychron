Pychron Introduction
========================

Overview
-------------
Pychron is an open-source system for automated data collection, hardware control,
and data reduction in noble gas mass spectrometry workflows. It is developed at the
New Mexico Geochronology Research Laboratory and is used primarily for Ar-Ar
geochronology and thermochronology applications.

The project combines:

- experiment queue construction and automated run execution
- laser and extraction-line control
- mass spectrometer integration
- DVC-backed data and repository workflows
- interactive plotting and reduction tools
- report, table, and figure export

Pychron is primarily implemented in Python and uses Qt for its desktop user
interface. The codebase is structured to support both instrument-facing workflows
and downstream analytical/reduction workflows.

Project Goals
------------------
Pychron exists to provide a maintainable, scriptable, and extensible alternative to
older closed or lightly documented laboratory software stacks. The project emphasizes:

- automation for routine and high-throughput analytical workflows
- traceable data handling and repository-backed persistence
- support for heterogeneous laboratory hardware
- reproducible reduction and reporting workflows
- an open development model with public source control and documentation

Architecture Notes
------------------
Pychron includes both user-facing applications and lower-level subsystems. Common
areas of the repository include:

- ``pychron/experiment`` for queue construction, automated runs, and execution
- ``pychron/pyscripts`` for measurement and extraction scripting
- ``pychron/dvc`` for repository and persistence workflows
- ``pychron/pipeline`` for reduction, plotting, and report generation
- ``pychron/hardware`` and related packages for device integration

For developer workflow and repository policy, see the developer guide.
