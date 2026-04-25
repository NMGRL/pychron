import unittest

from pychron.core.wait.wait_control import WaitControl


class WaitControlTestCase(unittest.TestCase):
    def test_stop_marks_control_canceled(self) -> None:
        control = WaitControl()

        control.stop()

        self.assertTrue(control.is_canceled())
        self.assertEqual(control.status, "canceled")

    def test_continue_wait_marks_control_continued(self) -> None:
        control = WaitControl()

        control.continue_wait()

        self.assertTrue(control.is_continued())
        self.assertEqual(control.status, "continued")
        self.assertEqual(control.current_time, 0)

    def test_set_message_updates_public_state(self) -> None:
        control = WaitControl()

        control.set_message("Waiting", color="blue")

        self.assertEqual(control.message, "Waiting")
        self.assertIn("0.0, 0.0, 1.0", str(control.message_color))


if __name__ == "__main__":
    unittest.main()
