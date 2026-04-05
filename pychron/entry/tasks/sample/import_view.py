from __future__ import annotations

from typing import TYPE_CHECKING

from pyface.constant import OK
from traits.api import Button, HasTraits, Instance, List, Property, Str, cached_property
from traitsui.api import EnumEditor, HGroup, Item, TableEditor, UItem, VGroup, View
from traitsui.table_column import ObjectColumn

from pychron.entry.tasks.sample.importer import (
    ACTION_LABELS,
    CANONICAL_FIELDS,
    MappingItem,
    SampleImportPreview,
    SampleImportRow,
    SampleImportService,
)

if TYPE_CHECKING:
    from pychron.entry.tasks.sample.sample_entry import SampleEntry


class SampleImportModel(HasTraits):
    owner = Instance("pychron.entry.tasks.sample.sample_entry.SampleEntry")
    service = Instance(SampleImportService)
    path = Str
    preview = Instance(SampleImportPreview)
    mappings = List(MappingItem)
    filter_action = Str("All")
    refresh_preview_button = Button("Refresh Preview")
    import_button = Button("Import Valid Rows")
    export_errors_button = Button("Export Errors")
    summary = Str

    filtered_rows = Property(depends_on="preview.rows_items, filter_action")
    can_import = Property(depends_on="preview.rows_items")
    can_export_errors = Property(depends_on="preview.rows_items")

    def load(self) -> None:
        parsed = self.service.parse_csv(self.path)
        self.mappings = self.service.build_mappings(parsed.headers)
        self.refresh_preview()

    def refresh_preview(self) -> None:
        self.preview = self.service.preview(self.path, self.mappings)
        self.summary = self.preview.summary_text

    def edit_traits(self, *args, **kw):
        self.load()
        return super(SampleImportModel, self).edit_traits(*args, **kw)

    def traits_view(self) -> View:
        mapping_columns = [
            ObjectColumn(name="source_header", label="Source Column", editable=False),
            ObjectColumn(
                name="target_field",
                label="Target Field",
                editor=EnumEditor(values=[""] + list(CANONICAL_FIELDS)),
            ),
        ]
        preview_columns = [
            ObjectColumn(name="source_row_index", label="Row", editable=False, width=60),
            ObjectColumn(name="action", label="Action", editable=False, width=70),
            ObjectColumn(name="sample", label="Sample", editable=False, width=130),
            ObjectColumn(name="project", label="Project", editable=False, width=130),
            ObjectColumn(name="material", label="Material", editable=False, width=100),
            ObjectColumn(name="principal_investigator", label="PI", editable=False, width=120),
            ObjectColumn(name="status_text", label="Summary", editable=False, width=380),
        ]
        preview_group = VGroup(
            HGroup(
                Item(
                    "filter_action",
                    editor=EnumEditor(values=list(ACTION_LABELS)),
                    label="Filter",
                ),
                UItem("refresh_preview_button"),
                UItem("import_button", enabled_when="can_import"),
                UItem("export_errors_button", enabled_when="can_export_errors"),
            ),
            UItem(
                "filtered_rows",
                editor=TableEditor(columns=preview_columns, editable=False),
                height=400,
            ),
            show_border=True,
            label="Preview",
        )

        return View(
            VGroup(
                Item("path", style="readonly", label="File"),
                Item("summary", style="readonly", show_label=False),
                VGroup(
                    UItem(
                        "mappings",
                        editor=TableEditor(
                            columns=mapping_columns,
                            sortable=False,
                            editable=True,
                            selection_mode="rows",
                        ),
                    ),
                    show_border=True,
                    label="Column Mapping",
                ),
                preview_group,
            ),
            title="Sample CSV Import",
            resizable=True,
            width=0.9,
            height=0.8,
            buttons=["OK", "Cancel"],
        )

    def _refresh_preview_button_fired(self) -> None:
        self.refresh_preview()

    def _import_button_fired(self) -> None:
        created = self.owner.commit_import_rows(self.preview.create_rows())
        self.refresh_preview()
        self.summary = "{} | Imported: {}".format(self.preview.summary_text, created)
        self.owner.information_dialog("Imported {} sample rows".format(created))

    def _export_errors_button_fired(self) -> None:
        path = self.owner.save_file_dialog(default_filename="sample_import_errors.csv")
        if path:
            self.service.export_rows(path, self.preview.error_rows(), self.preview.headers)
            self.owner.information_dialog("Exported error rows to {}".format(path))

    @cached_property
    def _get_filtered_rows(self) -> list[SampleImportRow]:
        if self.preview is None:
            return []
        return self.preview.rows_for_action(self.filter_action)

    @cached_property
    def _get_can_import(self) -> bool:
        return self.preview is not None and bool(self.preview.create_count)

    @cached_property
    def _get_can_export_errors(self) -> bool:
        return self.preview is not None and bool(self.preview.error_count)


def open_sample_import_dialog(owner: SampleEntry, path: str) -> bool:
    model = SampleImportModel(owner=owner, service=SampleImportService(owner.dvc), path=path)
    info = model.edit_traits()
    return info.result == OK
