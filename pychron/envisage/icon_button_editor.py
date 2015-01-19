from traitsui.editors import ButtonEditor
from traitsui.item import Item
from pychron.core.helpers.filetools import add_extension
from pychron.envisage.resources import icon

__author__ = 'ross'


def icon_button_editor(trait, name, label=None, editor_kw=None, **kw):
    if editor_kw is None:
        editor_kw = {}

    name = add_extension(name, '.png')
    # name = '{}.png'.format(name)
    kw['show_label'] = label is not None
    kw['label'] = label or ''
    image = icon(name)

    return Item(trait, style='custom',
                editor=ButtonEditor(image=image, **editor_kw),
                **kw)