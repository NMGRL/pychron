# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import warnings

warnings.simplefilter("ignore")

import sys
print sys.path

from ConfigParser import NoSectionError
from pyface.constant import OK
from traits.etsconfig.api import ETSConfig

ETSConfig.toolkit = "qt4"

from traitsui.qt4.table_editor import TableDelegate
from traitsui.qt4.extra import checkbox_renderer

import traits.has_traits

traits.has_traits.CHECK_INTERFACES = 1

from PySide import QtCore
from pyface.qt import QtGui
from traits.trait_base import Undefined
from traitsui.group import Group
from traitsui.qt4 import ui_panel


class _GroupPanel(object):
    """A sub-panel for a single group of items.  It may be either a layout or a
       widget.
    """

    def __init__(self, group, ui, suppress_label=False):
        """Initialise the object.
        """
        # Get the contents of the group:
        content = group.get_content()

        # Save these for other methods.
        self.group = group
        self.ui = ui

        if group.orientation == 'horizontal':
            self.direction = QtGui.QBoxLayout.LeftToRight
        else:
            self.direction = QtGui.QBoxLayout.TopToBottom

        # outer is the top-level widget or layout that will eventually be
        # returned.  sub is the QTabWidget or QToolBox corresponding to any
        # 'tabbed' or 'fold' layout.  It is only used to collapse nested
        # widgets.  inner is the object (not necessarily a layout) that new
        # controls should be added to.
        outer = sub = inner = None

        # Get the group label.
        if suppress_label:
            label = ""
        else:
            label = group.label

        # Create a border if requested.
        if group.show_border:
            outer = QtGui.QGroupBox(label)
            inner = QtGui.QBoxLayout(self.direction, outer)

        elif label != "":
            outer = inner = QtGui.QBoxLayout(self.direction)
            inner.addWidget(ui_panel.heading_text(None, text=label).control)

        # Add the layout specific content.
        if len(content) == 0:
            pass

        elif group.layout == 'flow':
            raise NotImplementedError, "'the 'flow' layout isn't implemented"

        elif group.layout == 'split':
            # Create the splitter.
            splitter = ui_panel._GroupSplitter(group)
            splitter.setOpaqueResize(False)  # Mimic wx backend resize behavior
            if self.direction == QtGui.QBoxLayout.TopToBottom:
                splitter.setOrientation(QtCore.Qt.Vertical)

            # Make sure the splitter will expand to fill available space
            policy = splitter.sizePolicy()
            policy.setHorizontalStretch(50)
            policy.setVerticalStretch(50)
            if group.orientation == 'horizontal':
                policy.setVerticalPolicy(QtGui.QSizePolicy.Expanding)
            else:
                policy.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
            splitter.setSizePolicy(policy)

            if outer is None:
                outer = splitter
            else:
                inner.addWidget(splitter)

            # Create an editor.
            editor = ui_panel.SplitterGroupEditor(control=outer, splitter=splitter, ui=ui)
            self._setup_editor(group, editor)

            self._add_splitter_items(content, splitter)

        elif group.layout in ('tabbed', 'fold'):
            # Create the TabWidget or ToolBox.
            if group.layout == 'tabbed':
                sub = QtGui.QTabWidget()
                sub.setProperty("traits_tabbed_group", True)
            else:
                sub = QtGui.QToolBox()

            # Give tab/tool widget stretch factor equivalent to default stretch
            # factory for a resizeable item. See end of '_add_items'.
            policy = sub.sizePolicy()
            policy.setHorizontalStretch(50)
            policy.setVerticalStretch(50)
            sub.setSizePolicy(policy)

            ui_panel._fill_panel(sub, content, self.ui, self._add_page_item)

            if outer is None:
                outer = sub
            else:
                inner.addWidget(sub)

            # Create an editor.
            editor = ui_panel.TabbedFoldGroupEditor(container=sub, control=outer, ui=ui)
            self._setup_editor(group, editor)

        else:
            # See if we need to control the visual appearance of the group.
            if group.visible_when != '' or group.enabled_when != '':
                # Make sure that outer is a widget and inner is a layout.
                # Hiding a layout is not properly supported by Qt (the
                # workaround in ``traitsui.qt4.editor._visible_changed_helper``
                # often leaves undesirable blank space).
                if outer is None:
                    outer = inner = QtGui.QBoxLayout(self.direction)

                if isinstance(outer, QtGui.QLayout):
                    widget = QtGui.QWidget()
                    widget.setLayout(outer)
                    outer = widget

                # Create an editor.
                self._setup_editor(group, ui_panel.GroupEditor(control=outer))

            if isinstance(content[0], Group):
                layout = self._add_groups(content, inner)
            else:
                layout = self._add_items(content, inner)
            layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

            if outer is None:
                outer = layout
            elif layout is not inner:
                inner.addLayout(layout)

        if group.style_sheet:
            if isinstance(outer, QtGui.QLayout):
                inner = outer
                outer = QtGui.QWidget()
                outer.setLayout(inner)

            # ensure this is not empty group
            if isinstance(outer, QtGui.QWidget):
                outer.setStyleSheet(group.style_sheet)

        # Publish the top-level widget, layout or None.
        self.control = outer

        # Publish the optional sub-control.
        self.sub_control = sub

    def _add_splitter_items(self, content, splitter):
        """Adds a set of groups or items separated by splitter bars.
        """
        for item in content:

            # Get a panel for the Item or Group.
            if isinstance(item, Group):
                panel = _GroupPanel(item, self.ui, suppress_label=True).control
            else:
                panel = self._add_items([item])

            # Add the panel to the splitter.
            if panel is not None:
                if isinstance(panel, QtGui.QLayout):
                    # A QSplitter needs a widget.
                    w = QtGui.QWidget()
                    panel.setContentsMargins(0, 0, 0, 0)
                    w.setLayout(panel)
                    panel = w

                layout = panel.layout()
                if layout is not None:
                    layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

                splitter.addWidget(panel)

    def _setup_editor(self, group, editor):
        """Setup the editor for a group.
        """
        if group.id != '':
            self.ui.info.bind(group.id, editor)

        if group.visible_when != '':
            self.ui.add_visible(group.visible_when, editor)

        if group.enabled_when != '':
            self.ui.add_enabled(group.enabled_when, editor)

    def _add_page_item(self, item, layout):
        """Adds a single Item to a page based panel.
        """
        self._add_items([item], layout)

    def _add_groups(self, content, outer):
        """Adds a list of Group objects to the panel, creating a layout if
           needed.  Return the outermost layout.
        """
        # Use the existing layout if there is one.
        if outer is None:
            outer = QtGui.QBoxLayout(self.direction)

        # Process each group.
        for subgroup in content:
            panel = _GroupPanel(subgroup, self.ui).control

            if isinstance(panel, QtGui.QWidget):
                outer.addWidget(panel)
            elif isinstance(panel, QtGui.QLayout):
                if isinstance(panel, QtGui.QBoxLayout):
                    if panel.direction() == QtGui.QBoxLayout.Down:
                        panel.setSpacing(0)
                outer.addLayout(panel)
            else:
                # The sub-group is empty which seems to be used as a way of
                # providing some whitespace.
                outer.addWidget(QtGui.QLabel(' '))

        outer.setSpacing(6)
        return outer

    def _add_items(self, content, outer=None):
        """Adds a list of Item objects, creating a layout if needed.  Return
           the outermost layout.
        """
        # Get local references to various objects we need:
        ui = self.ui
        info = ui.info
        handler = ui.handler

        group = self.group
        show_left = group.show_left
        columns = group.columns

        # See if a label is needed.
        show_labels = False
        for item in content:
            show_labels |= item.show_label

        # See if a grid layout is needed.
        if show_labels or columns > 1:
            inner = QtGui.QGridLayout()

            if outer is None:
                outer = inner
            else:
                outer.addLayout(inner)

            row = 0
            if show_left:
                label_alignment = QtCore.Qt.AlignRight
            else:
                label_alignment = QtCore.Qt.AlignLeft

        else:
            # Use the existing layout if there is one.
            if outer is None:
                outer = QtGui.QBoxLayout(self.direction)

            inner = outer

            row = -1
            label_alignment = 0

        # Process each Item in the list:
        col = -1
        for item in content:

            # Keep a track of the current logical row and column unless the
            # layout is not a grid.
            col += 1
            if row >= 0 and col >= columns:
                col = 0
                row += 1

            # Get the name in order to determine its type:
            name = item.name

            # Check if is a label:
            if name == '':
                label = item.label
                if label != "":

                    # Create the label widget.
                    if item.style == 'simple':
                        label = QtGui.QLabel(label)
                    else:
                        label = ui_panel.heading_text(None, text=label).control

                    self._add_widget(inner, label, row, col, show_labels)

                    if item.emphasized:
                        self._add_emphasis(label)

                # Continue on to the next Item in the list:
                continue

            # Check if it is a separator:
            if name == '_':
                cols = columns

                # See if the layout is a grid.
                if row >= 0:
                    # Move to the start of the next row if necessary.
                    if col > 0:
                        col = 0
                        row += 1

                    # Skip the row we are about to do.
                    row += 1

                    # Allow for the columns.
                    if show_labels:
                        cols *= 2

                for i in range(cols):
                    line = QtGui.QFrame()

                    if self.direction == QtGui.QBoxLayout.LeftToRight:
                        # Add a vertical separator:
                        line.setFrameShape(QtGui.QFrame.VLine)
                        if row < 0:
                            inner.addWidget(line)
                        else:
                            inner.addWidget(line, i, row)
                    else:
                        # Add a horizontal separator:
                        line.setFrameShape(QtGui.QFrame.HLine)
                        if row < 0:
                            inner.addWidget(line)
                        else:
                            inner.addWidget(line, row, i)

                    line.setFrameShadow(QtGui.QFrame.Sunken)

                # Continue on to the next Item in the list:
                continue

            # Convert a blank to a 5 pixel spacer:
            if name == ' ':
                name = '5'

            # Check if it is a spacer:
            if ui_panel.all_digits.match(name):

                # If so, add the appropriate amount of space to the layout:
                n = int(name)
                if self.direction == QtGui.QBoxLayout.LeftToRight:
                    # Add a horizontal spacer:
                    spacer = QtGui.QSpacerItem(n, 1)
                else:
                    # Add a vertical spacer:
                    spacer = QtGui.QSpacerItem(1, n)

                self._add_widget(inner, spacer, row, col, show_labels)

                # Continue on to the next Item in the list:
                continue

            # Otherwise, it must be a trait Item:
            object = eval(item.object_, globals(), ui.context)
            trait = object.base_trait(name)
            desc = trait.desc or ''

            # Get the editor factory associated with the Item:
            editor_factory = item.editor
            if editor_factory is None:
                editor_factory = trait.get_editor().set(**item.editor_args)

                # If still no editor factory found, use a default text editor:
                if editor_factory is None:
                    from traitsui.qt4.text_editor import ToolkitEditorFactory

                    editor_factory = ToolkitEditorFactory()

                # If the item has formatting traits set them in the editor
                # factory:
                if item.format_func is not None:
                    editor_factory.format_func = item.format_func

                if item.format_str != '':
                    editor_factory.format_str = item.format_str

                # If the item has an invalid state extended trait name, set it
                # in the editor factory:
                if item.invalid != '':
                    editor_factory.invalid = item.invalid

            # Create the requested type of editor from the editor factory:
            factory_method = getattr(editor_factory, item.style + '_editor')
            editor = factory_method(
                ui, object, name, item.tooltip, None
            ).set(item=item, object_name=item.object)

            # Tell the editor to actually build the editing widget.  Note that
            # "inner" is a layout.  This shouldn't matter as individual editors
            # shouldn't be using it as a parent anyway.  The important thing is
            # that it is not None (otherwise the main TraitsUI code can change
            # the "kind" of the created UI object).
            editor.prepare(inner)
            control = editor.control

            if item.style_sheet:
                control.setStyleSheet(item.style_sheet)

            # Set the initial 'enabled' state of the editor from the factory:
            editor.enabled = editor_factory.enabled

            # Handle any label.
            if item.show_label:
                label = self._create_label(item, ui, desc)
                self._add_widget(inner, label, row, col, show_labels,
                                 label_alignment)
            else:
                label = None

            editor.label_control = label

            # Add emphasis to the editor control if requested:
            if item.emphasized:
                self._add_emphasis(control)

            # Give the editor focus if it requested it:
            if item.has_focus:
                control.setFocus()

            # Set the correct size on the control, as specified by the user:
            stretch = 0
            item_width = item.width
            item_height = item.height
            if (item_width != -1) or (item_height != -1):
                is_horizontal = (self.direction == QtGui.QBoxLayout.LeftToRight)

                min_size = control.minimumSizeHint()
                width = min_size.width()
                height = min_size.height()

                force_width = False
                force_height = False

                if (0.0 < item_width <= 1.0) and is_horizontal:
                    stretch = int(100 * item_width)

                item_width = int(item_width)
                if item_width < -1:
                    item_width = -item_width
                    force_width = True
                else:
                    item_width = max(item_width, width)

                if (0.0 < item_height <= 1.0) and (not is_horizontal):
                    stretch = int(100 * item_height)

                item_height = int(item_height)
                if item_height < -1:
                    item_height = -item_height
                    force_height = True
                else:
                    item_height = max(item_height, height)

                control.setMinimumWidth(max(item_width, 0))
                control.setMinimumHeight(max(item_height, 0))
                if (stretch == 0 or not is_horizontal) and force_width:
                    control.setMaximumWidth(item_width)
                if (stretch == 0 or is_horizontal) and force_height:
                    control.setMaximumHeight(item_height)

            # Set size and stretch policies
            self._set_item_size_policy(editor, item, label, stretch)

            # Add the created editor control to the layout
            # FIXME: Need to decide what to do about border_size and padding
            self._add_widget(inner, control, row, col, show_labels)

            # ---- Update the UI object

            # Bind the editor into the UIInfo object name space so it can be
            # referred to by a Handler while the user interface is active:
            id = item.id or name
            info.bind(id, editor, item.id)

            self.ui._scrollable |= editor.scrollable

            # Also, add the editors to the list of editors used to construct
            # the user interface:
            ui._editors.append(editor)

            # If the handler wants to be notified when the editor is created,
            # add it to the list of methods to be called when the UI is
            # complete:
            defined = getattr(handler, id + '_defined', None)
            if defined is not None:
                ui.add_defined(defined)

            # If the editor is conditionally visible, add the visibility
            # 'expression' and the editor to the UI object's list of monitored
            # objects:
            if item.visible_when != '':
                ui.add_visible(item.visible_when, editor)

            # If the editor is conditionally enabled, add the enabling
            # 'expression' and the editor to the UI object's list of monitored
            # objects:
            if item.enabled_when != '':
                ui.add_enabled(item.enabled_when, editor)

        return outer

    def _set_item_size_policy(self, editor, item, label, stretch):
        """ Set size policy of an item and its label (if any).

        How it is set:

        1) The general rule is that we obey the item.resizable and
           item.springy settings. An item is considered resizable also if
           resizable is Undefined but the item is scrollable

        2) However, if the labels are on the right, and the item is of a
           kind that cannot be stretched in horizontal (e.g. a checkbox),
           we make the label stretchable instead (to avoid big gaps
           between element and label)

        If the item is resizable, the _GroupPanel is set to be resizable.
        """

        is_label_left = self.group.show_left

        is_item_resizable = (
            (item.resizable is True) or
            ((item.resizable is Undefined) and editor.scrollable))
        is_item_springy = item.springy

        # handle exceptional case 2)
        item_policy = editor.control.sizePolicy().horizontalPolicy()

        if label is not None and not is_label_left and item_policy == QtGui.QSizePolicy.Minimum:
            # this item cannot be stretched horizontally, and the label
            # exists and is on the right -> make label stretchable if necessary

            if self.direction == QtGui.QBoxLayout.LeftToRight and is_item_springy:
                is_item_springy = False
                self._make_label_h_stretchable(label, stretch or 50)

            elif (self.direction == QtGui.QBoxLayout.TopToBottom
                  and is_item_resizable):
                is_item_resizable = False
                self._make_label_h_stretchable(label, stretch or 50)

        if is_item_resizable:
            stretch = stretch or 50
            # FIXME: resizable is not defined as trait, were is it used?
            self.resizable = True
        elif is_item_springy:
            stretch = stretch or 50

        editor.set_size_policy(self.direction,
                               is_item_resizable, is_item_springy, stretch)
        return stretch

    def _make_label_h_stretchable(self, label, stretch):
        """ Set size policies of a QLabel to be stretchable horizontally.

        :attr:`stretch` is the stretch factor that Qt uses to distribute the
        total size to individual elements
        """
        label_policy = label.sizePolicy()
        label_policy.setHorizontalStretch(stretch)
        label_policy.setHorizontalPolicy(
            QtGui.QSizePolicy.Expanding)
        label.setSizePolicy(label_policy)

    def _add_widget(self, layout, w, row, column, show_labels,
                    label_alignment=QtCore.Qt.AlignmentFlag(0)):
        """Adds a widget to a layout taking into account the orientation and
           the position of any labels.
        """
        # If the widget really is a widget then remove any margin so that it
        # fills the cell.
        if isinstance(w, QtGui.QWidget):
            wl = w.layout()
            if wl is not None:
                wl.setContentsMargins(0, 0, 0, 0)

        # See if the layout is a grid.
        if row < 0:
            if isinstance(w, QtGui.QWidget):
                layout.addWidget(w)
            elif isinstance(w, QtGui.QLayout):
                layout.addLayout(w)
            else:
                layout.addItem(w)

        else:
            if self.direction == QtGui.QBoxLayout.LeftToRight:
                # Flip the row and column.
                row, column = column, row

            if show_labels:
                # Convert the "logical" column to a "physical" one.
                column *= 2

                # Determine whether to place widget on left or right of
                # "logical" column.
                if (label_alignment != 0 and not self.group.show_left) or \
                        (label_alignment == 0 and self.group.show_left):
                    column += 1

            if isinstance(w, QtGui.QWidget):
                layout.addWidget(w, row, column, label_alignment)
            elif isinstance(w, QtGui.QLayout):
                layout.addLayout(w, row, column, label_alignment)
            else:
                layout.addItem(w, row, column, 1, 1, label_alignment)

    def _create_label(self, item, ui, desc, suffix=':'):
        """Creates an item label.

        When the label is on the left of its component,
        it is not empty, and it does not end with a
        punctuation character (see :attr:`LABEL_PUNCTUATION_CHARS`),
        we append a suffix (by default a colon ':') at the end of the
        label text.

        We also set the help on the QLabel control (from item.help) and
        the tooltip (it item.desc exists; we add "Specifies " at the start
        of the item.desc string).

        Parameters
        ----------
        item : Item
            The item for which we want to create a label
        ui : UI
            Current ui object
        desc : string
            Description of the item, to create an appropriate tooltip
        suffix : string
            Characters to at the end of the label

        Returns
        -------
        label_control : QLabel
            The control for the label
        """

        label = item.get_label(ui)

        # append a suffix if the label is on the left and it does
        # not already end with a punctuation character
        if not (not (label != '') or not (label[-1] not in ui_panel.LABEL_PUNCTUATION_CHARS)) and self.group.show_left:
            label += suffix

        # create label controller
        label_control = QtGui.QLabel(label)

        if item.emphasized:
            self._add_emphasis(label_control)

        # FIXME: Decide what to do about the help.  (The non-standard wx way,
        # What's This style help, both?)
        # wx.EVT_LEFT_UP( control, show_help_popup )
        label_control.help = item.get_help(ui)

        # FIXME: do people rely on traitsui adding 'Specifies ' to the start
        # of every tooltip? It's not flexible at all
        if desc != '':
            label_control.setToolTip('Specifies ' + desc)

        return label_control

    def _add_emphasis(self, control):
        """Adds emphasis to a specified control's font.
        """
        # Set the foreground colour.
        pal = QtGui.QPalette(control.palette())
        pal.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0, 0, 127))
        control.setPalette(pal)

        # Set the font.
        font = QtGui.QFont(control.font())
        font.setBold(True)
        font.setPointSize(font.pointSize())
        control.setFont(font)


# # monkey patch ui_panel
# ui_panel._GroupPanel = _GroupPanel
class CheckboxRenderer(TableDelegate):
    """ A renderer which displays a checked-box for a True value and an
        unchecked box for a false value.
    """

    # ---------------------------------------------------------------------------
    #  QAbstractItemDelegate interface
    # ---------------------------------------------------------------------------

    def editorEvent(self, event, model, option, index):
        """ Reimplemented to handle mouse button clicks.
        """
        if event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
            column = index.model()._editor.columns[index.column()]
            obj = index.data(QtCore.Qt.UserRole)
            checked = bool(column.get_raw_value(obj))
            column.set_value(obj, not checked)
            return True
        else:
            return False

    def paint(self, painter, option, index):
        """ Reimplemented to paint the checkbox.
        """
        # Determine whether the checkbox is check or unchecked
        column = index.model()._editor.columns[index.column()]
        obj = index.data(QtCore.Qt.UserRole)
        checked = column.get_raw_value(obj)

        # First draw the background
        painter.save()
        row_brushes = [option.palette.base(), option.palette.alternateBase()]
        if option.state & QtGui.QStyle.State_Selected:
            bg_brush = option.palette.highlight()
        else:
            bg_brush = index.data(QtCore.Qt.BackgroundRole)
            if bg_brush == NotImplemented or bg_brush is None:
                if index.model()._editor.factory.alternate_bg_color:
                    bg_brush = row_brushes[index.row() % 2]
                else:
                    bg_brush = row_brushes[0]
        painter.fillRect(option.rect, bg_brush)

        # Then draw the checkbox
        style = QtGui.QApplication.instance().style()
        box = QtGui.QStyleOptionButton()
        box.palette = option.palette

        # Align the checkbox appropriately.
        box.rect = option.rect
        size = style.sizeFromContents(QtGui.QStyle.CT_CheckBox, box,
                                      QtCore.QSize(), None)
        box.rect.setWidth(size.width())
        margin = style.pixelMetric(QtGui.QStyle.PM_ButtonMargin, box)
        alignment = column.horizontal_alignment
        if alignment == 'left':
            box.rect.setLeft(option.rect.left() + margin)
        elif alignment == 'right':
            box.rect.setLeft(option.rect.right() - size.width() - margin)
        else:
            # FIXME: I don't know why I need the 2 pixels, but I do.
            box.rect.setLeft(option.rect.left() + option.rect.width() // 2 -
                             size.width() // 2 + margin - 2)

        box.state = QtGui.QStyle.State_Enabled | QtGui.QStyle.State_Active
        if checked:
            box.state |= QtGui.QStyle.State_On
        else:
            box.state |= QtGui.QStyle.State_Off
        style.drawControl(QtGui.QStyle.CE_CheckBox, box, painter)
        painter.restore()

    def sizeHint(self, option, index):
        """ Reimplemented to provide size hint based on a checkbox
        """
        box = QtGui.QStyleOptionButton()
        style = QtGui.QApplication.instance().style()
        return style.sizeFromContents(QtGui.QStyle.CT_CheckBox, box,
                                      QtCore.QSize(), None)


# monkey patch CheckboxColumn
checkbox_renderer.CheckboxRenderer = CheckboxRenderer

# ============= enthought library imports =======================
# ============= standard library imports ========================
import os
import sys
import logging
import subprocess
# ============= local library imports  ==========================
from pyface.message_dialog import information, warning
from pyface.confirmation_dialog import confirm

logger = logging.getLogger()


def entry_point(modname, klass, setup_version_id='', debug=False):
    """
        entry point
    """

    user = initialize_version(modname, debug)
    if user:
        if debug:
            set_commandline_args()

        # import app klass and pass to launch function
        if check_dependencies(debug):
            mod = __import__('pychron.applications.{}'.format(modname), fromlist=[klass])
            app = getattr(mod, klass)
            from pychron.envisage.pychron_run import launch

            launch(app, user)
    else:
        logger.critical('Failed to initialize user')


def check_dependencies(debug):
    """
        check the dependencies and install if possible/required
    """
    # suppress dependency checks temporarily
    return True

    with open('ENV.txt', 'r') as fp:
        env = fp.read().strip()

    ret = False
    logger.info('================ Checking Dependencies ================')
    for npkg, req in (('uncertainties', '2.1'),
                      ('pint', '0.5'),
                      # ('fant', '0.1')
                      ):
        try:
            pkg = __import__(npkg)
            ver = pkg.__version__
        except ImportError:
            if confirm(None, '"{}" is required. Attempt to automatically install?'.format(npkg)):
                if not install_package(pkg, env, debug):
                    warning(None, 'Failed installing "{}". Try to install manually'.format(npkg))
                    break

            else:
                warning(None, 'Install "{}" package. required version>={} '.format(npkg, req))
                break

        vargs = ver.split('.')
        maj = int(vargs[0])
        if maj < int(float(req)):
            warning(None, 'Update "{}" package. your version={}. required version>={} '.format(npkg, maj, req))
            break
        logger.info('{:<15s} >={:<5s} satisfied. Current ver: {}'.format(npkg, req, ver))
    else:
        ret = True

    logger.info('=======================================================')
    return ret


def install_package(pkg, env, debug):
    # this may not work when using conda environments
    # use absolute path to pip /anaconda/envs/.../bin/pip
    # use -n to specify environment

    if not subprocess.check_call(['conda', 'search', '{}'.format(pkg)], stdout=subprocess.PIPE):

        try:
            subprocess.check_call(['pip', 'install', '{}'.format(pkg)], stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return
    else:
        if debug:
            cmd = ['conda', 'install', '-yq', '{}'.format(pkg)]
        else:
            cmd = ['conda', 'install', '-yq', '-n', env, '{}'.format(pkg)]
        subprocess.check_call(cmd, stdout=subprocess.PIPE)

    if debug:
        cmd = ['conda', 'list']
    else:
        cmd = ['conda', 'list', '-n', env]

    deps = subprocess.check_output(cmd)
    for dep in deps.split('\n'):
        if dep.split(' ')[0] == pkg:
            logger.info('"{}" installed successfully'.format(pkg))
            return True


def set_commandline_args():
    from pychron.globals import globalv
    import argparse

    parser = argparse.ArgumentParser(description='Generate a password')
    parser.add_argument('-t', '--testbot',
                        action='store')
    args = parser.parse_args()
    globalv.use_testbot = args.testbot


def initialize_version(appname, debug):
    root = os.path.dirname(__file__)

    if not debug:
        add_eggs(root)
    else:
        build_sys_path()

    # can now use pychron.
    from pychron.envisage.user_login import get_user

    user = get_user()
    if not user:
        logger.info('user login failed')
        return

    if appname.startswith('py'):
        appname = appname[2:]

    from pychron.paths import paths

    pref_path = os.path.join(paths.base, '.enthought',
                             'pychron.{}.application.{}'.format(appname, user),
                             'preferences.ini')

    from ConfigParser import ConfigParser

    cp = ConfigParser()
    cp.read(pref_path)
    proot = None
    try:
        proot = cp.get('pychron.general', 'root_dir')
    except BaseException, e:
        print 'root_dir exception={}'.format(e)
        from pyface.directory_dialog import DirectoryDialog

        information(None, 'Pychron root directory not set in Preferences/General. Please select a valid directory')
        dlg = DirectoryDialog(action='open', default_directory=os.path.expanduser('~'))
        result = dlg.open()
        if result == OK:
            proot = str(dlg.path)

    if not proot:
        return False

    logger.debug('using Pychron root: {}'.format(proot))
    paths.build(proot)
    try:
        cp.set('pychron.general', 'root_dir', proot)
    except NoSectionError:
        cp.add_section('pychron.general')
        cp.set('pychron.general', 'root_dir', proot)

    root = os.path.dirname(pref_path)
    if not os.path.isdir(root):
        os.mkdir(root)

    with open(pref_path, 'w') as wfile:
        cp.write(wfile)

    # build globals
    build_globals(debug)

    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import build_directories

    # build directories
    build_directories()
    paths.write_defaults()

    # setup logging. set a basename for log files and logging level
    logging_setup('pychron', level='DEBUG')

    from pychron.core.helpers.exception_helper import set_exception_handler, report_issues
    set_exception_handler()
    report_issues()

    return user


def build_sys_path():
    """
        need to launch from terminal
    """

    sys.path.insert(0, os.path.dirname(os.getcwd()))


def add_eggs(root):
    egg_path = os.path.join(root, 'pychron.pth')
    if os.path.isfile(egg_path):
        # use a pychron.pth to get additional egg paths
        with open(egg_path, 'r') as rfile:
            eggs = [ei.strip() for ei in rfile.read().split('\n')]
            eggs = [ei for ei in eggs if ei]

            for egg_name in eggs:
                # sys.path.insert(0, os.path.join(root, egg_name))
                sys.path.append(os.path.join(root, egg_name))
                print os.path.join(root, egg_name)


def build_globals(debug):
    try:
        from pychron.envisage.initialization.initialization_parser import InitializationParser
    except ImportError, e:
        from pyface.message_dialog import warning

        warning(None, str(e))

    ip = InitializationParser()

    from pychron.globals import globalv

    globalv.build(ip)
    globalv.debug = debug

# ============= EOF =============================================
