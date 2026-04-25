import random

from traits.api import Button, HasTraits
from traitsui.api import View

from pychron.paths import paths
from pychron.pipeline.plot.editors.folium_map_figure_editor import MapFigureEditor
from pychron.pipeline.save_figure import SaveFigureModel, SaveFigureView


class _DemoAnalysis:
    def __init__(self):
        self.repository_identifier = random.choice(["Foo", "Bar", "Bat"])
        self.identifier = "1000"


class _SaveFigureDemo(HasTraits):
    test = Button

    def __init__(self, controller: SaveFigureView, model: SaveFigureModel, *args, **kw):
        self._controller = controller
        self._model = model
        super(_SaveFigureDemo, self).__init__(*args, **kw)

    def traits_view(self):
        return View("test")

    def _test_fired(self):
        self._controller.edit_traits()
        self._model.prepare_path()


def demo_save_figure() -> None:
    paths.build("_dev")
    analyses = [_DemoAnalysis() for _ in range(5)]
    model = SaveFigureModel(analyses)
    controller = SaveFigureView(model=model)
    _SaveFigureDemo(controller=controller, model=model).configure_traits()


def demo_folium_map() -> None:
    editor = MapFigureEditor()
    editor.load()
    editor.configure_traits()


if __name__ == "__main__":
    demo_save_figure()
