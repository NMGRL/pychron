import os
import tempfile
import unittest

try:
    from pychron.experiment.conditional.conditional import (
        conditionals_from_file,
        conditional_from_dict,
        TerminationConditional,
    )
    from pychron.experiment.conditional.groups import (
        ModificationGroup,
        TruncationGroup,
    )
except ModuleNotFoundError as exc:
    conditionals_from_file = None
    conditional_from_dict = None
    TerminationConditional = None
    ModificationGroup = None
    TruncationGroup = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class _Spec:
    analysis_type = "unknown"


class _Run:
    def __init__(self, analysis_type="unknown"):
        self.spec = _Spec()
        self.spec.analysis_type = analysis_type

    def get_interpolated_value(self, token):
        return token


@unittest.skipIf(_IMPORT_ERROR is not None, "Experiment traits stack not available")
class ConditionalConfigurationTestCase(unittest.TestCase):
    def test_analysis_types_allows_matching_non_blank_type(self):
        cond = conditional_from_dict(
            {"check": "device.pneumatics<80", "analysis_types": ["unknown"]},
            "TerminationConditional",
        )
        run = _Run("unknown")
        run.get_device_value = lambda name: 60
        self.assertTrue(cond.check(run, ([], []), 1000))

    def test_analysis_types_blank_alias_matches_blank_variants(self):
        cond = conditional_from_dict(
            {"check": "device.pneumatics<80", "analysis_types": ["blank"]},
            "TerminationConditional",
        )
        run = _Run("blank_unknown")
        run.get_device_value = lambda name: 60
        self.assertTrue(cond.check(run, ([], []), 1000))

    def test_conditionals_from_file_loads_modification_and_equilibration(self):
        fd, path = tempfile.mkstemp(suffix=".yaml")
        try:
            with os.fdopen(fd, "w") as wfile:
                wfile.write(
                    "modifications:\n"
                    "  - check: device.pneumatics<80\n"
                    "    action: Run Blank\n"
                    "equilibrations:\n"
                    "  - check: device.pneumatics<80\n"
                    "    abbreviated_count_ratio: 0.5\n"
                )

            conds = conditionals_from_file(path)

            self.assertIn("modifications", conds)
            self.assertIn("equilibrations", conds)
            self.assertEqual(conds["modifications"][0].action, "Run Blank")
            self.assertEqual(
                conds["equilibrations"][0].abbreviated_count_ratio,
                0.5,
            )
        finally:
            os.remove(path)

    def test_modification_group_ignores_selected_conditionals_without_action_fields(self):
        group = ModificationGroup([], editable=True, available_attrs=[])
        group.selected = TerminationConditional("Ar40>10")

        group._selected_changed_hook()

        self.assertEqual(group.action, "")

    def test_truncation_group_ignores_selected_conditionals_without_abbrev_field(self):
        group = TruncationGroup([], editable=True, available_attrs=[])
        group.selected = TerminationConditional("Ar40>10")

        group._selected_changed_hook()

        self.assertEqual(group.abbreviated_count_ratio, 0.0)


if __name__ == "__main__":
    unittest.main()
