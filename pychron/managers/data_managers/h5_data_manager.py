# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Any
# ============= standard library imports ========================
from tables import open_file, Filters
# ============= local library imports  ==========================
from data_manager import DataManager
from table_descriptions import table_description_factory
import os
import weakref


def get_table(name, group, frame):
    try:
        if isinstance(group, str):
            group = getattr(frame.root, group)
        return getattr(group, name)
    except AttributeError:
        try:
            return getattr(frame.root, name)
        except AttributeError:
            pass


class TableCTX(object):
    def __init__(self, p, t, g, complevel, mode):
        self._file = open_file(p, mode,
                               filters=Filters(complevel=complevel))
        self._t = t
        self._g = g

    def __enter__(self):
        return get_table(self._t, self._g, self._file)

    def __exit__(self, *args):
        self._file.close()
        del self._file


class FileCTX(object):
    def __init__(self, parent, p, m, complevel):
        self._file = open_file(p, m,
                               filters=Filters(complevel=complevel))
        self._parent = parent
        self._parent._frame = self._file

    def __enter__(self):
        return self._file

    def __exit__(self, *args, **kw):
        if not self._parent._file_stack or len(self._parent._file_stack) < 2:
            self._parent.close_file()
            self._file.close()
            self._parent._file_stack.pop()
        else:
            self._parent._file_stack.pop()

        del self._file
        del self._parent


class H5DataManager(DataManager):
    """
    """
    #    _extension = 'h5'
    _extension = 'hdf5'
    repository = Any
    workspace_root = None
    compression_level = 5

    def __init__(self, *args, **kw):
        super(H5DataManager, self).__init__(*args, **kw)
        self._file_stack = []

    def set_group_attribute(self, group, key, value):
        f = self._frame

        if isinstance(group, str):
            group = getattr(f, group)

        setattr(group._v_attrs, key, value)

    def record(self, values, table):
        """

        """
        _df, ptable = self._get_parent(table)
        nr = ptable.row
        for key in values:
            nr.__setitem__(key, values[key])

        nr.append()
        ptable.flush()

    def get_current_path(self):
        if self._frame is not None:
            return self._frame.filename

    def lock_path(self, p):
        import stat

        os.chmod(p, stat.S_IROTH | stat.S_IRGRP | stat.S_IREAD)

    def delete_frame(self):
        p = self.get_current_path()
        try:
            os.remove(p)
        except Exception, e:
            print 'exception', e

    def new_frame_ctx(self, *args, **kw):
        p = self._new_frame_path(*args, **kw)
        return self.open_file(p, 'w')

    def new_frame(self, *args, **kw):
        """

        """
        p = self._new_frame_path(*args, **kw)
        try:
            self._frame = open_file(p, mode='w')

            return self._frame
        except ValueError:
            pass

    def new_group(self, group_name, parent=None, description=''):
        """
            if group already exists return it otherwise create a new group
        """
        if parent is None:
            parent = self._frame.root

        grp = self.get_group(group_name, parent)

        if grp is None:
            grp = self._frame.create_group(parent, group_name, description)

        return grp

    def new_table(self, group, table_name, n=None, table_style='TimeSeries'):
        """
            if table already exists return it otherwise create a new table
        """
        tab = self.get_table(table_name, group)
        if tab is None:
            tab = self._frame.create_table(group, table_name,
                                           table_description_factory(table_style),
                                           expectedrows=n or 10000)

        tab.flush()
        return tab

    def new_array(self, group, name, data):
        self._frame.create_array(group, name, data)

    def get_table(self, name, group, frame=None):
        if frame is None:
            frame = self._frame

        # self.debug('get table name={} group={} frame={}'.format(name, group, str(frame)[:80]))
        return get_table(name, group, frame)

    def get_group(self, name, grp=None):
        return next((g for g in self.get_groups(grp=grp) if g._v_name == name), None)

    def get_groups(self, grp=None):
        if grp is not None:
            if isinstance(grp, str):
                grp = getattr(self._frame.root, grp)
                #            print 'wget', grp
            return [g for g in grp._f_walk_groups() if g != grp]
        else:
            return [g for g in self._frame.walk_groups() if g != self._frame.root]

    def get_tables(self, grp):
        if isinstance(grp, str):
            grp = '/{}'.format(grp)

        f = self._frame
        return [n for n in f.walk_nodes(grp, 'Table')]

    def isfile(self, path):
        return os.path.isfile(path)

    def open_data(self, path, mode='r'):
        if self.repository:
            out = os.path.join(self.workspace_root, path)
            path = os.path.join(self.repository.root, path)
            if not os.path.isfile(out):
                self.info('copying {} to repository {}'.format(path, os.path.dirname(out)))
                if not self.repository.retrieveFile(path, out):
                    return False
            path = out

        try:
            self._frame = open_file(path, mode, filters=Filters(complevel=self.compression_level))
            return True
        except Exception:
            self._frame = None
            import traceback
            traceback.print_exc()
            return True

    def close_file(self):
        try:
            self.debug('flush and close file {}'.format(self._frame.filename))

            for node in self._frame.walk_nodes('/', 'Table'):
                node.flush()

            self._frame.flush()
            self._frame.close()
            self._frame = None

        except Exception, e:
            print 'exception closing file', e

    def open_file(self, path, mode='r+'):
        self._file_stack.append(1)
        return FileCTX(weakref.ref(self)(), path, mode, self.compression_level)

    def open_table(self, path, table, group='/', mode='r'):
        return TableCTX(path, table, group, self.compression_level, mode)

    def kill(self):
        self.close_file()


if __name__ == '__main__':
    d = H5DataManager()
    print d

# ============= EOF ====================================
