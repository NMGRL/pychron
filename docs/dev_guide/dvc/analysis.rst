Analysis
===========


example. See also https://github.com/NMGRLData/Lusk01121/blob/master/666/81-03L.json

.. code-block:: json

    {
        "acquisition_software": "pychron py3/18.2",
        "aliquot": 3,
        "analysis_type": "unknown",
        "analyst_name": "",
        "arar_mapping": {
            "Ar36": "Ar36",
            "Ar37": "Ar37",
            "Ar38": "Ar38",
            "Ar39": "Ar39",
            "Ar40": "Ar40"
        },
        "collection_version": "1.0:2.0",
        "comment": "C:16 Muscovite, fine, 4.98 mg",
        "commit": "f3c45de575b8ae63b7fee625a0156943968ccbb4",
        "conditionals": [
            {
                "analysis_types": [],
                "frequency": 10,
                "hash_id": -3426856737248020020,
                "level": 10,
                "location": "setupfiles/spectrometer/default_conditionals.yaml",
                "ntrips": 1,
                "start_count": 5,
                "teststr": "L2(CDD).deflection==3250"
            }
        ],
        "data_reduction_software": "pychron py3/18.2",
        "detectors": {
            "AX": {
                "deflection": 0.0,
                "gain": 1
            },
            "H1": {
                "deflection": 0.0,
                "gain": 1
            },
            "H2": {
                "deflection": 0.0,
                "gain": 1
            },
            "L1": {
                "deflection": 0.0,
                "gain": 1
            },
            "L2(CDD)": {
                "deflection": 0.0,
                "gain": 1
            }
        },
        "environmental": {
            "lab_humiditys": [
                {
                    "device": "EnvironmentalMonitor",
                    "name": "Lab Hum.",
                    "pub_date": "2019-03-15T07:53:04",
                    "title": "iServer Hum.",
                    "value": 18.3
                }
            ],
            "lab_pneumatics": [
                {
                    "device": "AirPressure",
                    "name": "Pressure",
                    "pub_date": "2019-03-15T12:43:35",
                    "title": "Building",
                    "value": 101.1
                },
                {
                    "device": "AirPressure2",
                    "name": "Pressure2",
                    "pub_date": "2019-03-15T07:53:04",
                    "title": "Lab",
                    "value": 87.5
                },
                {
                    "device": "MicroBoneGaugeController",
                    "name": "JanDecabinPressure",
                    "pub_date": "2019-03-15T07:53:04",
                    "title": "Jan Decabin",
                    "value": 2.0
                }
            ],
            "lab_temperatures": []
        },
        "experiment_queue_name": "LoadLF0001",
        "experiment_type": "Ar/Ar",
        "extraction": "felix_furnace.py",
        "grainsize": "",
        "identifier": "66681",
        "increment": 11,
        "instrument_name": "",
        "intensity_scalar": 0.0,
        "irradiation": "NM-300",
        "irradiation_level": "C",
        "irradiation_position": 16,
        "isotopes": {
            "Ar36": {
                "detector": "L2(CDD)",
                "name": "Ar36",
                "serial_id": "00000"
            },
            "Ar37": {
                "detector": "L1",
                "name": "Ar37",
                "serial_id": "00000"
            },
            "Ar38": {
                "detector": "AX",
                "name": "Ar38",
                "serial_id": "00000"
            },
            "Ar39": {
                "detector": "H1",
                "name": "Ar39",
                "serial_id": "00000"
            },
            "Ar40": {
                "detector": "H2",
                "name": "Ar40",
                "serial_id": "00000"
            }
        },
        "laboratory": "",
        "latitude": "",
        "lithology": "",
        "lithology_class": "",
        "lithology_group": "",
        "lithology_type": "",
        "longitude": "",
        "mass_spectrometer": "felix",
        "material": "",
        "measurement": "felix_analysis340_60_CDD_center.py",
        "post_equilibration": "felix_pump_extraction_line.py",
        "post_measurement": "felix_pump_ms.py",
        "principal_investigator": "",
        "project": "",
        "queue_conditionals_name": "",
        "repository_identifier": "Lusk01121",
        "rlocation": null,
        "sample": "LS-248",
        "source": {
            "emission": 770.169,
            "trap": 248.607
        },
        "spec_sha": "857b14d91aad9a1d167c9a6f53bb8f032c5a9e87",
        "timestamp": "2019-03-15T14:49:55.061740",
        "tripped_conditional": null,
        "unit": null,
        "username": "",
        "uuid": "a251fda6-5bd9-4c5d-bb5b-c77bcd8dbaec",
        "whiff_result": null
    }