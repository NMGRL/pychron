# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
# ============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.progress_dialog import myProgressDialog


class CancelLoadingError(BaseException):
    pass


def open_progress(n, close_at_end=True):
    pd = myProgressDialog(max=n - 1,
                          #dialog_size=(0,0, 550, 15),
                          close_at_end=close_at_end,
                          can_cancel=True,
                          can_ok=True)
    pd.open()
    return pd


def progress_loader(xs, func, threshold=50, progress=None, reraise_cancel=False):
    """
        xs: list or tuple
        func: callable with signature func(xi, prog, i, n)
            where xi is ith item of xs, prog is a progress_dialog, i is ith iteration and n is total iterations

        threshold: trigger value to open a progress dialog i.e. if n>threshold open the dialog
        progress: an existing progress_dialog
        reraise_cancel: if canceled during iteration should the exception be reraised for all objects to handle

        return: list

        if user clicks "Cancel" during iteration an empty list is returned
        if user clicks "Accept" during iteration a partial list is returned

    """

    def gen(prog):
        n = len(xs)
        if n > threshold or prog:
            if not prog:
                prog = open_progress(n)

            for i, x in enumerate(xs):
                if prog.canceled:
                    raise CancelLoadingError
                elif prog.accepted:
                    break
                yield func(x, prog, i, n)
        else:
            for x in xs:
                yield func(x, None, 0, 0)

    try:
        return list(gen(progress))
    except CancelLoadingError:
        if reraise_cancel:
            raise CancelLoadingError
        else:
            return []


def progress_iterator(xs, func, threshold=50, progress=None, reraise_cancel=False):
    """
        see progress_loader documentation

        only difference is that this function does not return anything
    """

    def gen(prog):
        n = len(xs)
        if n > threshold or prog:
            if not prog:
                prog = open_progress(n)

            for i, x in enumerate(xs):
                if prog.canceled:
                    raise CancelLoadingError
                elif prog.accepted:
                    break
                func(x, prog, i, n)
        else:
            for x in xs:
                func(x, None, 0, 0)

    try:
        gen(progress)
    except CancelLoadingError:
        if reraise_cancel:
            raise CancelLoadingError

#============= EOF =============================================



