Easy Tools
===========

"Easy" tools are convient way to batch edits to the database or batch produce figures and/or tables. "Easy" tools are noninteractive and
are configured prior to running using a YAML configuration file

Here is an example "Easy" configuration file

.. code-block:: YAML

    #=========================================================================================
    # Setup
    #=========================================================================================
    root: minna_bluff

    ---
    #=========================================================================================
    # Imports
    #=========================================================================================
    source:
     database: massspecdata_minnabluff
     username: root
     password: Argon
     host: localhost

    destination:
     database: pychrondata_minnabluff
     username: root
     password: Argon
     host: localhost

    irradiations:
      - name: NM-205
        levels: E,F,G,H,O
      - name: NM-213
        levels: A,C,I,J,K,L
      - name: NM-216
        levels: C,D,E,F
      - name: NM-220
        levels: L,M,N,O
      - name: NM-222
        levels: A,B,C,D
      - name: NM-256
        levels: E,F

    imports:
      atype: unknown
      airs: True
      cocktails: True
      blanks: True
      cocktail_blanks: True
      air_blanks: True
      dry_run: False

    ---
    #=========================================================================================
    # Iso Fits
    #=========================================================================================

    projects:
     - Minna Bluff

    #use x if you mean seconds
    #use n if you mean counts
    #use d if you mean endtime-starttime
    fit_isotopes:
    # - name: Ar40
    #    fit: '"parabolic" if x>150 else "linear"'
    #  - name: Ar39
    #    fit: '"parabolic" if x>150 else "linear"'
    #  - name: Ar38
    #    fit: '"parabolic" if x>150 else "linear"'
    #  - name: Ar37
    #    fit: '"parabolic" if x>150 else "linear"'
    #  - name: Ar36
    #    fit: '"parabolic" if x>150 else "linear"'
      - name: Ar40
        fit: '"parabolic" if x>150 else "linear"'
      - name: Ar39
        fit: '"parabolic" if x>150 else "linear"'
      - name: Ar38
        fit: '"linear" if x>150 else "linear"'
      - name: Ar37
        fit: '"linear" if x>150 else "linear"'
      - name: Ar36
        fit: '"parabolic" if x>150 else "linear"'
      - name: Ar40bs
        fit: average_SEM
      - name: Ar39bs
        fit: average_SEM
      - name: Ar38bs
        fit: average_SEM
      - name: Ar37bs
        fit: average_SEM
      - name: Ar36bs
        fit: average_SEM

    filter_isotopes:
      - name: Ar40
        use: True
        n: 1
        std_devs: 2
      - name: Ar39
        use: True
        n: 1
        std_devs: 2
      - name: Ar38
        use: True
        n: 1
        std_devs: 2
      - name: Ar37
        use: True
        n: 1
        std_devs: 2
      - name: Ar36
        use: True
        n: 1
        std_devs: 2
      - name: Ar40bs
        use: True
        n: 1
        std_devs: 2
      - name: Ar39bs
        use: True
        n: 1
        std_devs: 2
      - name: Ar38bs
        use: True
        n: 1
        std_devs: 2
      - name: Ar37bs
        use: True
        n: 1
        std_devs: 2
      - name: Ar36bs
        use: True
        n: 1
        std_devs: 2

    ---
    #=========================================================================================
    # Blanks
    #=========================================================================================

    projects:
      - Minna Bluff

    blank_fit_isotopes:
      - name: Ar40
        fit: preceding
      - name: Ar39
        fit: preceding
      - name: Ar38
        fit: preceding
      - name: Ar37
        fit: preceding
      - name: Ar36
        fit: preceding

    ---
    #=========================================================================================
    # Discrimination
    #=========================================================================================

    projects:
       - Minna Bluff

    discrimination: [1.004, 0.001]
    detector: Multiplier Analog

    ---
    #=========================================================================================
    # Figures
    #=========================================================================================
    projects:
      - J

    options:
      ideogram: Default
      spectrum: Default

    ---
    #=========================================================================================
    # Tables
    #=========================================================================================

    projects:
      - Minna Bluff

    file_types:
      - pdf
      - csv
      - xls

    options:
      ideogram: Default

The configuration file is divided into multiple YAML "documents" separated by ``---``.
These "documents" are

#. Setup
#. Import
#. Iso Fits
#. Blanks
#. Discrimination
#. Figures
#. Tables
