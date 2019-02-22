Interpreted Ages
=====================

JSON format
-------------

.. code-block:: json

    {
    "analyses": [
        {
            "age": float,
            "age_err": float,
            "age_err_wo_j": float,
            "baseline_corrected_intercepts": {},
            "blanks": {},
            "ic_corrected_values": {},
            "icfactors": {},
            "interference_corrected_values": {},
            "kca": float,
            "kca_err": float,
            "kcl": float,
            "kcl_err": float,
            "plateau_step": false,
            "radiogenic_yield": float,
            "radiogenic_yield_err": float,
            "record_id": str,
            "tag": str,
            "uuid": str
        },

    ],
    "name": str,
    "preferred": {
        "age": float,
        "age_err": float,
        "ages": {
            "integrated_age": float,
            "integrated_age_err": float,
            "isochron_age": float,
            "isochron_age_err": float,
            "plateau_age": float,
            "plateau_age_err": float,
            "weighted_age": float,
            "weighted_age_err": float
        },
        "arar_constants": {
            "abundance_sensitivity": float,
            "atm4036": float,
            "atm4036_err": float,
            "atm4038": float,
            "atm4038_err": float,
            "fixed_k3739": float,
            "fixed_k3739_err": float,
            "lambda_Ar37": float,
            "lambda_Ar37_err": float,
            "lambda_Ar39": float,
            "lambda_Ar39_err": float,
            "lambda_Cl36": float,
            "lambda_Cl36_err": float,
            "lambda_k": float,
            "lambda_k_err": float
        },
        "display_age_units": str,
        "include_j_error_in_mean": bool,
        "include_j_error_in_plateau": bool,
        "include_j_position_error": bool,
        "mswd": float,
        "nanalyses": int,
        "preferred_kinds": [
            {
                "attr": <"age", "kca", "kcl", "radiogenic_yield", "moles_k39", "signal_k39"
                "error": float,
                "error_kind": <"SD", "SEM", "SEM, but if MSWD>1 use SEM * sqrt(MSWD)">,
                "kind": <"Weighted Mean", >,
                "value": float,
                "weighting": str
            },

        ]
    },
    "sample_metadata": {
        "grainsize": str,
        "irradiation": str,
        "irradiation_level": str,
        "irradiation_position": int,
        "latitude": float,
        "lithology": str,
        "lithology_class": str,
        "lithology_group": str,
        "lithology_type": str,
        "longitude": float,
        "material": str,
        "principal_investigator": str,
        "project": str,
        "rlocation": str,
        "sample": str
    },
    "uuid": str
    }


Example
-------------
.. code-block:: json

    {
    "analyses": [
        {
            "age": 27.719555312784266,
            "age_err": 0.48224260012401765,
            "age_err_wo_j": 0.48224260012401765,
            "baseline_corrected_intercepts": {
                "Ar36": {
                    "error": 0.0005994962038630668,
                    "value": 0.04723067451378344
                },
                "Ar37": {
                    "error": 0.005503939925822024,
                    "value": 0.11309640278377814
                },
                "Ar38": {
                    "error": 0.002341430315982881,
                    "value": 0.2361151444228655
                },
                "Ar39": {
                    "error": 0.013954133127184293,
                    "value": 15.974211414208787
                },
                "Ar40": {
                    "error": 0.01590441601008484,
                    "value": 74.78410787929032
                },
                "Ar41": {
                    "error": 0.0015305403722731324,
                    "value": 0.013232090318390084
                }
            },
            "blanks": {
                "Ar36": {
                    "error": 0.002530676861539285,
                    "value": 0.026285578599641108
                },
                "Ar37": {
                    "error": 0.00786620718599018,
                    "value": 0.03449851337958194
                },
                "Ar38": {
                    "error": 0.004198981148223098,
                    "value": 0.01028580551619398
                },
                "Ar39": {
                    "error": 0.012217213055969865,
                    "value": 0.01441814607864897
                },
                "Ar40": {
                    "error": 0.7319125809914061,
                    "value": 7.196981549647406
                },
                "Ar41": {
                    "error": 0.0033257704726891275,
                    "value": 0.0298623430332032
                }
            },
            "ic_corrected_values": {
                "Ar36": {
                    "error": 0.0026156461984591295,
                    "value": 0.02106494810372595
                },
                "Ar37": {
                    "error": 0.009600550515464271,
                    "value": 0.07859788940419621
                },
                "Ar38": {
                    "error": 0.004807674969019501,
                    "value": 0.2258293389066715
                },
                "Ar39": {
                    "error": 0.0189981835950715,
                    "value": 15.963026765621615
                },
                "Ar40": {
                    "error": 0.7320853615953016,
                    "value": 67.58712632964291
                },
                "Ar41": {
                    "error": 0.0036610521804761047,
                    "value": -0.016630252714813117
                }
            },
            "icfactors": {
                "Ar36": {
                    "error": 0.0007633894469259384,
                    "value": 1.0057222077222714
                },
                "Ar37": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar38": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar39": {
                    "error": 0.00025692197839542535,
                    "value": 1.0002026027177893
                },
                "Ar40": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar41": {
                    "error": 1e-20,
                    "value": 1.0
                }
            },
            "interference_corrected_values": {
                "Ar36": {
                    "error": 0.0026156750775804503,
                    "value": 0.021023296922508376
                },
                "Ar37": {
                    "error": 0.017507863602034712,
                    "value": 0.14333351953315343
                },
                "Ar38": {
                    "error": 0.004807674969019972,
                    "value": 0.225827734744206
                },
                "Ar39": {
                    "error": 0.019002275618033367,
                    "value": 15.966353214167436
                },
                "Ar40": {
                    "error": 0.7321010417064032,
                    "value": 67.48517797176511
                },
                "Ar41": {
                    "error": 0.0,
                    "value": 0.0
                }
            },
            "kca": 57.86448398141012,
            "kca_err": 7.199353476239163,
            "kcl": 1758.301586538721,
            "kcl_err": 213.78707269155652,
            "plateau_step": false,
            "radiogenic_yield": 90.56231365030379,
            "radiogenic_yield_err": 1.1600258740023146,
            "record_id": "66714-01A",
            "tag": "ok",
            "uuid": "e4edbbed-1fae-413d-9d29-42bd6553f61a"
        },
        {
            "age": 27.19176900710652,
            "age_err": 0.011303308461930284,
            "age_err_wo_j": 0.011303308461930284,
            "baseline_corrected_intercepts": {
                "Ar36": {
                    "error": 0.0005885739390490279,
                    "value": 0.03852176691264056
                },
                "Ar37": {
                    "error": 0.0057490619669011075,
                    "value": 3.45429957981653
                },
                "Ar38": {
                    "error": 0.0033829188468008317,
                    "value": 10.134664901311618
                },
                "Ar39": {
                    "error": 0.056042465844671034,
                    "value": 892.6225273747481
                },
                "Ar40": {
                    "error": 0.12363467388955417,
                    "value": 3373.5458784531465
                },
                "Ar41": {
                    "error": 0.0015080380730257462,
                    "value": 0.12610673955911397
                }
            },
            "blanks": {
                "Ar36": {
                    "error": 0.002530676861621177,
                    "value": 0.02616848527176168
                },
                "Ar37": {
                    "error": 0.00786620718599018,
                    "value": 0.03449851337958194
                },
                "Ar38": {
                    "error": 0.004198981148223098,
                    "value": 0.01028580551619398
                },
                "Ar39": {
                    "error": 0.012217213055969865,
                    "value": 0.01441814607864897
                },
                "Ar40": {
                    "error": 0.7319126030362056,
                    "value": 7.161701124116693
                },
                "Ar41": {
                    "error": 0.0033257704726891275,
                    "value": 0.0298623430332032
                }
            },
            "ic_corrected_values": {
                "Ar36": {
                    "error": 0.002613104085564699,
                    "value": 0.012423969684479709
                },
                "Ar37": {
                    "error": 0.009743147796897693,
                    "value": 3.419801066436948
                },
                "Ar38": {
                    "error": 0.005392177909451174,
                    "value": 10.124379095795424
                },
                "Ar39": {
                    "error": 0.22919253475203238,
                    "value": 892.7479146167714
                },
                "Ar40": {
                    "error": 0.7422813422624946,
                    "value": 3366.3841773290296
                },
                "Ar41": {
                    "error": 0.003651702078032389,
                    "value": 0.09624439652591077
                }
            },
            "icfactors": {
                "Ar36": {
                    "error": 0.0007633894469259384,
                    "value": 1.0057222077222714
                },
                "Ar37": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar38": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar39": {
                    "error": 0.000248593700629227,
                    "value": 1.0001566257203542
                },
                "Ar40": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar41": {
                    "error": 1e-20,
                    "value": 1.0
                }
            },
            "interference_corrected_values": {
                "Ar36": {
                    "error": 0.0026131461049083635,
                    "value": 0.010708269470396504
                },
                "Ar37": {
                    "error": 0.017770194313444784,
                    "value": 6.237256451140361
                },
                "Ar38": {
                    "error": 0.005392177909499971,
                    "value": 10.124289479023856
                },
                "Ar39": {
                    "error": 0.22924186600949456,
                    "value": 892.9352934062675
                },
                "Ar40": {
                    "error": 0.7891411431378178,
                    "value": 3360.6826069310478
                },
                "Ar41": {
                    "error": 0.0,
                    "value": 0.0
                }
            },
            "kca": 74.75390813988191,
            "kca_err": 0.39479729918549195,
            "kcl": -81096.19073918163,
            "kcl_err": 45898.849977837715,
            "plateau_step": false,
            "radiogenic_yield": 99.73566732777049,
            "radiogenic_yield_err": 0.024504026259052673,
            "record_id": "66714-01B",
            "tag": "ok",
            "uuid": "07db433f-1ef3-4f9f-a86b-4257bc7b66ec"
        },
        {
            "age": 28.077041834912727,
            "age_err": 1.0831169368560338,
            "age_err_wo_j": 1.0831169368560338,
            "baseline_corrected_intercepts": {
                "Ar36": {
                    "error": 0.0004299589870458764,
                    "value": 0.028314796367070936
                },
                "Ar37": {
                    "error": 0.005602722653107384,
                    "value": 0.0806406276715168
                },
                "Ar38": {
                    "error": 0.0024130480783469245,
                    "value": 0.12608958192546776
                },
                "Ar39": {
                    "error": 0.013245702205643093,
                    "value": 7.070455599926101
                },
                "Ar40": {
                    "error": 0.013957558105976904,
                    "value": 35.249057192632584
                },
                "Ar41": {
                    "error": 0.0016832882633947878,
                    "value": 0.012745520931239408
                }
            },
            "blanks": {
                "Ar36": {
                    "error": 0.002530676861972484,
                    "value": 0.025626797314095968
                },
                "Ar37": {
                    "error": 0.00786620718599018,
                    "value": 0.03449851337958194
                },
                "Ar38": {
                    "error": 0.004198981148223098,
                    "value": 0.01028580551619398
                },
                "Ar39": {
                    "error": 0.012217213055969865,
                    "value": 0.01441814607864897
                },
                "Ar40": {
                    "error": 0.7319126965606669,
                    "value": 6.998865020529088
                },
                "Ar41": {
                    "error": 0.0033257704726891275,
                    "value": 0.0298623430332032
                }
            },
            "ic_corrected_values": {
                "Ar36": {
                    "error": 0.002581631171217421,
                    "value": 0.0027033803419133596
                },
                "Ar37": {
                    "error": 0.009657521246187668,
                    "value": 0.04614211429193487
                },
                "Ar38": {
                    "error": 0.004842958157112939,
                    "value": 0.11580377640927378
                },
                "Ar39": {
                    "error": 0.01809056121293549,
                    "value": 7.055615611059068
                },
                "Ar40": {
                    "error": 0.7320457696175756,
                    "value": 28.250192172103496
                },
                "Ar41": {
                    "error": 0.003727493610282049,
                    "value": -0.017116822101963792
                }
            },
            "icfactors": {
                "Ar36": {
                    "error": 0.0007633894469259384,
                    "value": 1.0057222077222714
                },
                "Ar37": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar38": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar39": {
                    "error": 0.0002284464313923612,
                    "value": 0.999940215341664
                },
                "Ar40": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar41": {
                    "error": 1e-20,
                    "value": 1.0
                }
            },
            "interference_corrected_values": {
                "Ar36": {
                    "error": 0.0025816598854381256,
                    "value": 0.0026782432606453515
                },
                "Ar37": {
                    "error": 0.017624693242188124,
                    "value": 0.08420798467278917
                },
                "Ar38": {
                    "error": 0.004842958157113373,
                    "value": 0.11580306623350124
                },
                "Ar39": {
                    "error": 0.018094462938368167,
                    "value": 7.057073121479985
                },
                "Ar40": {
                    "error": 0.7320488406202872,
                    "value": 28.205131349099723
                },
                "Ar41": {
                    "error": 0.0,
                    "value": 0.0
                }
            },
            "kca": 43.33891696981006,
            "kca_err": 9.195528920548588,
            "kcl": 890.4075256113907,
            "kcl_err": 124.47542755103413,
            "plateau_step": false,
            "radiogenic_yield": 97.01001764226808,
            "radiogenic_yield_err": 2.729519464106105,
            "record_id": "66714-02A",
            "tag": "ok",
            "uuid": "3d0fc7d9-fdbe-4273-91d4-3d08fa3d3875"
        },
        {
            "age": 27.20578856468821,
            "age_err": 0.008984828080871995,
            "age_err_wo_j": 0.008984828080871995,
            "baseline_corrected_intercepts": {
                "Ar36": {
                    "error": 0.0005156569867258774,
                    "value": 0.03268865013767039
                },
                "Ar37": {
                    "error": 0.006285618771135262,
                    "value": 4.692054070934782
                },
                "Ar38": {
                    "error": 0.0035473824640944057,
                    "value": 14.668141452121183
                },
                "Ar39": {
                    "error": 0.0714188158731977,
                    "value": 1296.8816804669736
                },
                "Ar40": {
                    "error": 0.1495589243817402,
                    "value": 4896.041232850392
                },
                "Ar41": {
                    "error": 0.001549585156482157,
                    "value": 0.1839271092016435
                }
            },
            "blanks": {
                "Ar36": {
                    "error": 0.002530676862038943,
                    "value": 0.025514325015847744
                },
                "Ar37": {
                    "error": 0.00786620718599018,
                    "value": 0.03449851337958194
                },
                "Ar38": {
                    "error": 0.004198981148223098,
                    "value": 0.01028580551619398
                },
                "Ar39": {
                    "error": 0.012217213055969865,
                    "value": 0.01441814607864897
                },
                "Ar40": {
                    "error": 0.7319127140768318,
                    "value": 6.965135517701946
                },
                "Ar41": {
                    "error": 0.0033257704726891275,
                    "value": 0.0298623430332032
                }
            },
            "ic_corrected_values": {
                "Ar36": {
                    "error": 0.0025974627554178,
                    "value": 0.0072153781004368235
                },
                "Ar37": {
                    "error": 0.010069072391683928,
                    "value": 4.657555557555201
                },
                "Ar38": {
                    "error": 0.005496850464556723,
                    "value": 14.65785564660499
                },
                "Ar39": {
                    "error": 0.3053349690822899,
                    "value": 1296.7304212151641
                },
                "Ar40": {
                    "error": 0.7470368751872541,
                    "value": 4889.07609733269
                },
                "Ar41": {
                    "error": 0.0036690548366303676,
                    "value": 0.1540647661684403
                }
            },
            "icfactors": {
                "Ar36": {
                    "error": 0.0007633894469259384,
                    "value": 1.0057222077222714
                },
                "Ar37": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar38": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar39": {
                    "error": 0.0002287167863376534,
                    "value": 0.9998944833371105
                },
                "Ar40": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar41": {
                    "error": 1e-20,
                    "value": 1.0
                }
            },
            "interference_corrected_values": {
                "Ar36": {
                    "error": 0.002597519173467174,
                    "value": 0.004883069506186372
                },
                "Ar37": {
                    "error": 0.018378118561798284,
                    "value": 8.50098975988744
                },
                "Ar38": {
                    "error": 0.005496850464641618,
                    "value": 14.657725507807312
                },
                "Ar39": {
                    "error": 0.30540076957693696,
                    "value": 1297.0033286855808
                },
                "Ar40": {
                    "error": 0.8422989275748238,
                    "value": 4880.794471732948
                },
                "Ar41": {
                    "error": 0.0,
                    "value": 0.0
                }
            },
            "kca": 79.79005818318248,
            "kca_err": 0.4144529334766862,
            "kcl": -49088.79633100066,
            "kcl_err": 16638.294686564474,
            "plateau_step": false,
            "radiogenic_yield": 99.8007955734752,
            "radiogenic_yield_err": 0.017746891705874197,
            "record_id": "66714-02B",
            "tag": "ok",
            "uuid": "3c110d6c-e8ea-4947-8561-ad8df56f48f6"
        },
        {
            "age": 27.05196522081795,
            "age_err": 0.10183095672511248,
            "age_err_wo_j": 0.10183095672511248,
            "baseline_corrected_intercepts": {
                "Ar36": {
                    "error": 0.001704049992893757,
                    "value": 0.4254132837797189
                },
                "Ar37": {
                    "error": 0.005890772322284931,
                    "value": 2.421729792372489
                },
                "Ar38": {
                    "error": 0.0021662585558443427,
                    "value": 1.1360499350201467
                },
                "Ar39": {
                    "error": 0.020065294937529957,
                    "value": 83.83985323379515
                },
                "Ar40": {
                    "error": 0.039711915054936875,
                    "value": 440.7745775100887
                },
                "Ar41": {
                    "error": 0.0016883051991301717,
                    "value": 0.029795339207878906
                }
            },
            "blanks": {
                "Ar36": {
                    "error": 0.0025306768621025056,
                    "value": 0.025402549702945698
                },
                "Ar37": {
                    "error": 0.00786620718599018,
                    "value": 0.03449851337958194
                },
                "Ar38": {
                    "error": 0.004198981148223098,
                    "value": 0.01028580551619398
                },
                "Ar39": {
                    "error": 0.012217213055969865,
                    "value": 0.01441814607864897
                },
                "Ar40": {
                    "error": 0.7319127307822177,
                    "value": 6.931643673110177
                },
                "Ar41": {
                    "error": 0.0033257704726891275,
                    "value": 0.0298623430332032
                }
            },
            "ic_corrected_values": {
                "Ar36": {
                    "error": 0.0030835352429197617,
                    "value": 0.40229967858829874
                },
                "Ar37": {
                    "error": 0.009827431711587812,
                    "value": 2.387231278992907
                },
                "Ar38": {
                    "error": 0.00472484061253941,
                    "value": 1.1257641295039527
                },
                "Ar39": {
                    "error": 0.030420992914993072,
                    "value": 83.81275660236166
                },
                "Ar40": {
                    "error": 0.7329892780105407,
                    "value": 433.84293383697855
                },
                "Ar41": {
                    "error": 0.003729761880123292,
                    "value": -6.700382532429452e-05
                }
            },
            "icfactors": {
                "Ar36": {
                    "error": 0.0007633894469259384,
                    "value": 1.0057222077222714
                },
                "Ar37": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar38": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar39": {
                    "error": 0.00023062248286486071,
                    "value": 0.9998487513325571
                },
                "Ar40": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar41": {
                    "error": 1e-20,
                    "value": 1.0
                }
            },
            "interference_corrected_values": {
                "Ar36": {
                    "error": 0.0030835688313353674,
                    "value": 0.4010702882022748
                },
                "Ar37": {
                    "error": 0.01793936914076707,
                    "value": 4.357742862409555
                },
                "Ar38": {
                    "error": 0.0047248406125404915,
                    "value": 1.1257555095051646
                },
                "Ar39": {
                    "error": 0.030427563432013357,
                    "value": 83.82768763313119
                },
                "Ar40": {
                    "error": 0.7334205869901604,
                    "value": 433.3076772888897
                },
                "Ar41": {
                    "error": 0.0,
                    "value": 0.0
                }
            },
            "kca": 9.844837783377043,
            "kca_err": 0.041208242888349955,
            "kcl": 3879.757091962007,
            "kcl_err": 220.00581486326422,
            "plateau_step": false,
            "radiogenic_yield": 72.2759597316246,
            "radiogenic_yield_err": 0.21926992957115193,
            "record_id": "66714-03A",
            "tag": "ok",
            "uuid": "353ecedf-1138-491d-b00a-708627bb1d17"
        },
        {
            "age": 27.257140377955807,
            "age_err": 0.009870173988038862,
            "age_err_wo_j": 0.009870173988038862,
            "baseline_corrected_intercepts": {
                "Ar36": {
                    "error": 0.0011740404627554493,
                    "value": 0.17608560651941374
                },
                "Ar37": {
                    "error": 0.0066242839210119125,
                    "value": 8.655850950817861
                },
                "Ar38": {
                    "error": 0.003368833749325161,
                    "value": 13.104874179515685
                },
                "Ar39": {
                    "error": 0.06709999536211372,
                    "value": 1141.7321025755205
                },
                "Ar40": {
                    "error": 0.14601043577843667,
                    "value": 4361.511631866489
                },
                "Ar41": {
                    "error": 0.0015375250230911944,
                    "value": 0.14729125332300214
                }
            },
            "blanks": {
                "Ar36": {
                    "error": 0.002530676862163096,
                    "value": 0.02529147137538983
                },
                "Ar37": {
                    "error": 0.00786620718599018,
                    "value": 0.03449851337958194
                },
                "Ar38": {
                    "error": 0.004198981148223098,
                    "value": 0.01028580551619398
                },
                "Ar39": {
                    "error": 0.012217213055969865,
                    "value": 0.01441814607864897
                },
                "Ar40": {
                    "error": 0.7319127466664469,
                    "value": 6.8983894867537785
                },
                "Ar41": {
                    "error": 0.0033257704726891275,
                    "value": 0.0298623430332032
                }
            },
            "ic_corrected_values": {
                "Ar36": {
                    "error": 0.002808072473526074,
                    "value": 0.15165701050861827
                },
                "Ar37": {
                    "error": 0.010283888027351354,
                    "value": 8.62135243743828
                },
                "Ar38": {
                    "error": 0.005383352441901346,
                    "value": 13.09458837399949
                },
                "Ar39": {
                    "error": 0.2758636521557973,
                    "value": 1141.4927881127328
                },
                "Ar40": {
                    "error": 0.7463345872254825,
                    "value": 4354.613242379735
                },
                "Ar41": {
                    "error": 0.0036639776791954452,
                    "value": 0.11742891028979893
                }
            },
            "icfactors": {
                "Ar36": {
                    "error": 0.0007633894469259384,
                    "value": 1.0057222077222714
                },
                "Ar37": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar38": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar39": {
                    "error": 0.00023412359079403406,
                    "value": 0.9998030193280036
                },
                "Ar40": {
                    "error": 1e-20,
                    "value": 1.0
                },
                "Ar41": {
                    "error": 1e-20,
                    "value": 1.0
                }
            },
            "interference_corrected_values": {
                "Ar36": {
                    "error": 0.0028081313819327625,
                    "value": 0.14726825995280343
                },
                "Ar37": {
                    "error": 0.018775005530363115,
                    "value": 15.739758580779586
                },
                "Ar38": {
                    "error": 0.0053833524419721265,
                    "value": 13.094473362585436
                },
                "Ar39": {
                    "error": 0.2759231389141926,
                    "value": 1141.7272701964312
                },
                "Ar40": {
                    "error": 0.8211803243999938,
                    "value": 4347.323085460973
                },
                "Ar41": {
                    "error": 0.0,
                    "value": 0.0
                }
            },
            "kca": 37.44364818670555,
            "kca_err": 0.09445756296981635,
            "kcl": 81362.83610704304,
            "kcl_err": 45829.61448767505,
            "plateau_step": false,
            "radiogenic_yield": 98.82289562480149,
            "radiogenic_yield_err": 0.020825217118115198,
            "record_id": "66714-03B",
            "tag": "ok",
            "uuid": "3a0f1610-a843-471d-982c-ac5ff9db3fd9"
        }
    ],
    "name": "01",
    "preferred": {
        "age": 27.21904871046781,
        "age_err": 0.014539368948486097,
        "ages": {
            "integrated_age": 27.224606105198074,
            "integrated_age_err": 0.04786378364736604,
            "isochron_age": 27.220009733430548,
            "isochron_age_err": 0.016358126816747635,
            "plateau_age": 27.19980252231228,
            "plateau_age_err": 0.0070158804430981905,
            "weighted_age": 27.21904871046781,
            "weighted_age_err": 0.014539368948486097
        },
        "arar_constants": {
            "abundance_sensitivity": 1e-07,
            "atm4036": 298.56,
            "atm4036_err": 0.31,
            "atm4038": 1583.87,
            "atm4038_err": 3.01,
            "fixed_k3739": 0.00013,
            "fixed_k3739_err": 0.011,
            "lambda_Ar37": 0.0197500001,
            "lambda_Ar37_err": 0.01,
            "lambda_Ar39": 7.0680001e-06,
            "lambda_Ar39_err": 0.01,
            "lambda_Cl36": 6.308e-09,
            "lambda_Cl36_err": 0.0,
            "lambda_k": 5.464e-10,
            "lambda_k_err": 0.0
        },
        "display_age_units": "Ma",
        "include_j_error_in_mean": true,
        "include_j_error_in_plateau": true,
        "include_j_position_error": false,
        "mswd": 5.4587149741362255,
        "nanalyses": 6,
        "preferred_kinds": [
            {
                "attr": "age",
                "error": 0.014539368948486097,
                "error_kind": "SEM, but if MSWD>1 use SEM * sqrt(MSWD)",
                "kind": "Weighted Mean",
                "value": 27.21904871046781,
                "weighting": ""
            },
            {
                "attr": "kca",
                "error": 5.786677620450036,
                "error_kind": "SEM, but if MSWD>1 use SEM * sqrt(MSWD)",
                "kind": "Weighted Mean",
                "value": 15.338441091495552,
                "weighting": ""
            },
            {
                "attr": "kcl",
                "error": 539.3999618451804,
                "error_kind": "SEM, but if MSWD>1 use SEM * sqrt(MSWD)",
                "kind": "Weighted Mean",
                "value": 1642.7849155072458,
                "weighting": ""
            },
            {
                "attr": "radiogenic_yield",
                "error": 0.6851802497583488,
                "error_kind": "SEM, but if MSWD>1 use SEM * sqrt(MSWD)",
                "kind": "Weighted Mean",
                "value": 99.3902152923649,
                "weighting": ""
            },
            {
                "attr": "moles_k39",
                "error": 3.1218504932975703e-15,
                "error_kind": "SEM, but if MSWD>1 use SEM * sqrt(MSWD)",
                "kind": "Weighted Mean",
                "value": 2.328687191170094e-15,
                "weighting": ""
            },
            {
                "attr": "signal_k39",
                "error": 39.02313116621963,
                "error_kind": "SEM, but if MSWD>1 use SEM * sqrt(MSWD)",
                "kind": "Weighted Mean",
                "value": 29.108589889626177,
                "weighting": ""
            }
        ]
    },
    "sample_metadata": {
        "grainsize": "",
        "irradiation": "NM-300",
        "irradiation_level": "F",
        "irradiation_position": 9,
        "latitude": 72.0,
        "lithology": "tuff",
        "lithology_class": "igneous",
        "lithology_group": "felsic",
        "lithology_type": "volcanic",
        "longitude": 106.0,
        "material": "Sanidine",
        "principal_investigator": "Zimmerer, M",
        "project": "AdvancedArgonFall2018",
        "rlocation": "",
        "sample": "04L-37 JM w/ inclusion"
    },
    "uuid": "a8ea1025-01af-4d9a-8fff-b4235a14ce62"
    }

