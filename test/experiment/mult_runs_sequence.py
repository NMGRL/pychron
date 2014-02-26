__author__ = 'ross'

import unittest

'''
*	Version 7.75	Marker denoting start of set-up parameters
CO2	Heating device name (see Calibration file)
145-hole	Sample holder file
0	Timed delay before beginning multiple-runs
30	Timed delay between runs
3	Number of unknowns between blanks
0	Number of unknowns between air-pipette analyses (0=no air pipettes)
0	Number of unknowns between detector gain intercalibrations (0=none)
False	Start with blank?
False	End with blank?
40	Time at full heating intensity
0	Rise time to full heating intensity
0.025	Maximum Ar40 background intensity
5	Maximum number of successive background runs above maximum intensity threshold
0	Maximum Ar40 hot blank intensity
300	Maximum unknown signal intensity (any isotope)
-0.001	Minimum Ar40 intensity, background or unknown
False	Overlap runs (True/False)
10	Delay following equilibration before starting overlap extraction
False	Overlap onto blanks (True/False)
60	Minimum time for pumping of extraction line between overlap samples
120	Delay at first stage of sample cleanup
120	Delay at second stage of sample cleanup
True	Analyze second extraction-line stage only?
True	Two-stage cleanup?
False	Video-capture laser heating?
3	Curtail run after x cycles if conditions are met
False	Curtail if 37Ar/39Ar > condition?
1	Curtail conditional value for 37Ar/39Ar
False	Curtail if %40Ar* < condition?
50	Curtail conditional value for %40Ar*
False	Curtail if 39Ar signal < condition?
0.1	Curtail conditional value for 39Ar signal
False	Curtail if Age (Ma) > condition?
100	Curtail conditional value for Age maximum
False	Curtail if Age (Ma) < condition?
0	Curtail conditional value for Age minimum
Unknown (12 cycle 36 first)	Spectrometer set-up file for unknown (and blanks)
Air (6 cycle before)	Spectrometer set-up file for air pipette runs
none	Jog specification file name
(Unused)
Note that a line with just a 'B' or an 'A' will force a blank or an air to be done at that point.
Run ID	Sample	Comment	Run script	1st stage (s)	2nd stage (s)	Power	Beam Dia.	Time at temp. (s)	Degas	Jog	Laser off/on	Scan	X-Y pos.	Holes / Scan
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		65
B
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		67
B
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		68
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		69
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		70
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		71
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		72
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		73
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		74
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		75
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		76
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		77
18747	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		78
18748	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		46
18748	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		47
18748	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		48
18748	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		49
18748	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		50
18748	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		51
18748	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		52
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		53
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		54
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		55
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		56
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		57
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		58
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		59
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		60
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		61
18749	FC-2	Sanidine, single crystal	Unknown			3.2	0		False	False	False	False		62
'''


class MultRunsSequenceTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
