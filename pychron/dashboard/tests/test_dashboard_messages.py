import unittest

from pychron.dashboard.messages import (
    CONFIG_KIND,
    VALUE_KIND,
    decode_config_payload,
    decode_event_message,
    encode_config_payload,
    encode_event,
    make_event,
    parse_legacy_message,
)


class _Config(object):
    def as_payload(self):
        return {
            "source_path": "/tmp/dashboard.yaml",
            "port": 8100,
            "devices": [
                {
                    "name": "Env",
                    "device": "environmental_monitor",
                    "enabled": True,
                    "values": [
                        {
                            "name": "temperature",
                            "tag": "<Env,temperature>",
                            "func_name": "get_temperature",
                            "period": 10,
                            "enabled": True,
                            "threshold": 0.1,
                            "units": "C",
                            "timeout": 60.0,
                            "record": False,
                            "bindname": "",
                            "conditionals": [],
                        }
                    ],
                }
            ],
        }


class DashboardMessagesTestCase(unittest.TestCase):
    def test_event_round_trip(self):
        event = make_event(VALUE_KIND, tag="<Env,temperature>", value=10.5)
        payload = encode_event(event)
        decoded = decode_event_message(payload)
        self.assertEqual(decoded["kind"], VALUE_KIND)
        self.assertEqual(decoded["tag"], "<Env,temperature>")

    def test_config_round_trip(self):
        payload = encode_config_payload(_Config())
        decoded = decode_config_payload(payload)
        self.assertEqual(decoded["port"], 8100)
        self.assertEqual(decoded["devices"][0]["name"], "Env")

    def test_parse_legacy_error_message(self):
        event = parse_legacy_message("error Pump failure")
        self.assertEqual(event["kind"], "error")
        self.assertEqual(event["message"], "Pump failure")

    def test_parse_legacy_value_message(self):
        event = parse_legacy_message("<Env,temperature> 11.25")
        self.assertEqual(event["kind"], VALUE_KIND)
        self.assertEqual(event["value"], "11.25")


if __name__ == "__main__":
    unittest.main()
