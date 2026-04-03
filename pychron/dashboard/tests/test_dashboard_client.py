import unittest

try:
    from pychron.dashboard.client import DashboardClient
    from pychron.dashboard.messages import encode_event, make_event
except ModuleNotFoundError as exc:
    DashboardClient = None
    encode_event = None
    make_event = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


PAYLOAD = {
    "devices": [
        {
            "name": "Env",
            "device": "environmental_monitor",
            "enabled": True,
            "values": [
                {
                    "name": "temperature",
                    "tag": "<Env,temperature>",
                    "units": "C",
                }
            ],
        }
    ]
}


@unittest.skipIf(_IMPORT_ERROR is not None, str(_IMPORT_ERROR))
class DashboardClientTestCase(unittest.TestCase):
    def test_structured_value_update_updates_value(self):
        client = DashboardClient()
        client._load_configuration_payload(PAYLOAD)
        event = encode_event(
            make_event("value_update", tag="<Env,temperature>", value=12.5, units="C")
        )
        client._handle_dashboard_message(event.split(" ", 1)[1])
        self.assertEqual(client.values[0].value, 12.5)
        self.assertFalse(client.values[0].timed_out)

    def test_timeout_marks_value_stale(self):
        client = DashboardClient()
        client._load_configuration_payload(PAYLOAD)
        event = encode_event(make_event("timeout", tag="<Env,temperature>"))
        client._handle_dashboard_message(event.split(" ", 1)[1])
        self.assertTrue(client.values[0].timed_out)
        self.assertTrue(client.values[0].stale)


if __name__ == "__main__":
    unittest.main()
