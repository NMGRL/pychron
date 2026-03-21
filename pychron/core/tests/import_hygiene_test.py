import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ImportHygieneTestCase(unittest.TestCase):
    def test_qt_editors_do_not_use_legacy_qt_imports(self):
        files = (
            ROOT / "pychron/core/ui/qt/double_spinner.py",
            ROOT / "pychron/core/ui/qt/label_editor.py",
            ROOT / "pychron/core/ui/qt/animated_png_editor.py",
            ROOT / "pychron/core/ui/qt/keyword_editor.py",
            ROOT / "pychron/core/ui/qt/keybinding_editor.py",
            ROOT / "pychron/core/ui/qt/patch_editor.py",
            ROOT / "pychron/core/ui/qt/display_editor.py",
        )
        for path in files:
            source = path.read_text()
            self.assertNotIn("from PySide import", source, path.as_posix())
            self.assertNotIn("import PySide", source, path.as_posix())
            self.assertNotIn("traitsui.qt4", source, path.as_posix())

    def test_library_modules_do_not_execute_top_level_demo_code(self):
        files = (
            ROOT / "pychron/core/stats/age_bracket.py",
            ROOT / "pychron/core/stats/peak_deconvolution.py",
        )
        for path in files:
            tree = ast.parse(path.read_text(), filename=path.as_posix())
            for node in tree.body:
                self.assertFalse(
                    self._is_top_level_call(node),
                    "{} has executable top-level code".format(path.as_posix()),
                )

    def test_runtime_modules_do_not_use_debug_prints(self):
        files = (
            ROOT / "pychron/experiment/automated_run/spec.py",
            ROOT / "pychron/gis/qgis_figure_editor.py",
            ROOT / "pychron/extraction_line/section.py",
            ROOT / "pychron/pipeline/data_reduction_logbook.py",
            ROOT / "pychron/graph/regression_graph.py",
        )
        for path in files:
            tree = ast.parse(path.read_text(), filename=path.as_posix())
            visitor = _RuntimePrintVisitor()
            visitor.visit(tree)
            self.assertFalse(visitor.found_print, path.as_posix())

    @staticmethod
    def _is_top_level_call(node):
        if isinstance(node, ast.Expr):
            return isinstance(node.value, ast.Call)
        if isinstance(node, ast.Assign):
            return isinstance(node.value, ast.Call)
        if isinstance(node, ast.AugAssign):
            return isinstance(node.value, ast.Call)
        return False


class _RuntimePrintVisitor(ast.NodeVisitor):
    def __init__(self):
        self.found_print = False
        self._inside_main_guard = False

    def visit_If(self, node):
        previous = self._inside_main_guard
        if _is_main_guard(node):
            self._inside_main_guard = True
        self.generic_visit(node)
        self._inside_main_guard = previous

    def visit_Call(self, node):
        if (
            not self._inside_main_guard
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ):
            self.found_print = True
        self.generic_visit(node)


def _is_main_guard(node):
    test = getattr(node, "test", None)
    if not isinstance(test, ast.Compare):
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
        return False
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    if len(test.comparators) != 1:
        return False
    comparator = test.comparators[0]
    return isinstance(comparator, ast.Constant) and comparator.value == "__main__"


if __name__ == "__main__":
    unittest.main()
