import unittest
from datetime import datetime

from pychron.pychron_constants import ATONA
from pychron.spectrometer.isotopx.spectrometer.ngx import NGXSpectrometer


class DummyController:
    triggered = False
    canceled = False

    def clear_canceled(self):
        self.canceled = False

    def stop_acquisition(self):
        self.triggered = False
        self.canceled = True

    def begin_acquisition(self):
        self.triggered = True
        self.canceled = False


class DummyDetector:
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind


class NGXAcquisitionTestCase(unittest.TestCase):
    def setUp(self):
        self.spec = NGXSpectrometer()
        self.spec.rcs_id = "NOM"
        self.spec.integration_time = 10
        self.spec.microcontroller = DummyController()
        self.spec.detectors = [
            DummyDetector("H2", "Faraday"),
            DummyDetector("CDD", "CDD"),
            DummyDetector("L2", ATONA),
        ]

    def test_parse_acq_event(self):
        targeta, targetb = self.spec._get_acquisition_targets()
        payload = "#EVENT:ACQ,NOM,foo,bar,12:34:56.789,1.0,2.0,3.0"
        parsed = self.spec._parse_acquisition_event(payload, targeta, targetb)
        self.assertEqual(parsed["kind"], "ACQ")
        self.assertEqual(parsed["signals"], [1.0, 2.0, 3.0])
        self.assertIsInstance(parsed["collection_time"], datetime)

    def test_reject_malformed_event(self):
        targeta, targetb = self.spec._get_acquisition_targets()
        payload = "#EVENT:ACQ,NOM,foo"
        self.assertIsNone(self.spec._parse_acquisition_event(payload, targeta, targetb))

    def test_filter_acq_uses_only_cdd_and_atona_when_present(self):
        self.spec.has_atonas = True
        signals, keys = self.spec._filter_signals_for_event("ACQ", [1.0, 2.0, 3.0])
        self.assertEqual(signals, [1.0, 2.0])
        self.assertEqual(keys, ["L2", "CDD"])

    def test_filter_acqb_keeps_all_channels(self):
        self.spec.has_atonas = True
        signals, keys = self.spec._filter_signals_for_event("ACQ.B", [1.0, 2.0, 3.0])
        self.assertEqual(signals, [1.0, 2.0, 3.0])
        self.assertEqual(keys, ["L2", "CDD", "H2"])

    def test_read_timeout_scales_with_integration_time(self):
        self.spec.integration_time = 20
        self.assertGreaterEqual(self.spec._get_read_timeout(), 20)

    def test_stale_event_detection_uses_collection_time_progression(self):
        t1 = datetime(2024, 1, 1, 12, 0, 1)
        t0 = datetime(2024, 1, 1, 12, 0, 0)
        self.assertFalse(self.spec._is_stale_event(t1))
        self.assertTrue(self.spec._is_stale_event(t0))

    def test_repeated_stale_events_reset_acquisition(self):
        self.spec.microcontroller.triggered = True
        self.spec._stale_event_count = self.spec._max_stale_event_count - 1
        self.assertTrue(self.spec._handle_stale_event(datetime(2024, 1, 1, 12, 0, 0)))
        self.assertFalse(self.spec.microcontroller.triggered)
        self.assertTrue(self.spec.microcontroller.canceled)

    def test_prepare_for_intensity_read_clears_canceled(self):
        self.spec.microcontroller.canceled = True
        self.spec._prepare_for_intensity_read()
        self.assertFalse(self.spec.microcontroller.canceled)


if __name__ == "__main__":
    unittest.main()
