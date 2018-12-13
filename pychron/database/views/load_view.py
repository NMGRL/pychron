from traits.api import HasTraits, Any, Property
from traitsui.api import View, UItem, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.helpers.traitsui_shortcuts import okcancel_view


class BaseView(ColumnSorterMixin):
    selected = Any
    title = ''
    _tabular_adapter_klass = TabularAdapter
    width = 500
    height = 300

    def traits_view(self):
        v = okcancel_view(UItem('records', editor=self._get_editor()),
                          title=self.title,
                          kind='livemodal',
                          resizable=True, width=self.width, height=self.height)
        return v

    def _get_editor(self):
        ed = TabularEditor(selected='selected',
                           column_clicked='column_clicked',
                           adapter=self._get_adapter())
        return ed

    def _get_adapter(self):
        a = self._tabular_adapter_klass(columns=self._get_columns())
        return a

    def _get_columns(self):
        raise NotImplementedError


class LoadAdapter(TabularAdapter):
    username_text = Property

    def _get_username_text(self):
        return self.item.username or ''


class LoadView(BaseView):
    title = 'Loads'
    _tabular_adapter_klass = LoadAdapter

    def _get_columns(self):
        return [('Load Name', 'name'),
                ('Holder', 'holderName'),
                ('Date', 'create_date'),
                ('User', 'username')]
