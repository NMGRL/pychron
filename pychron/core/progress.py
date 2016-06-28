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
# ============= local library imports  ==========================

from pychron.core.ui.progress_dialog import myProgressDialog


class CancelLoadingError(BaseException):
    pass


def open_progress(n, close_at_end=True, busy=False, **kw):
    if busy:
        mi, ma = 0, 0
    else:
        mi, ma = 0, n - 1

    pd = myProgressDialog(min=mi, max=ma,
                          close_at_end=close_at_end,
                          can_cancel=True,
                          can_ok=True, **kw)
    pd.open()
    return pd


def progress_loader(xs, func, threshold=50, progress=None,
                    use_progress=True,
                    reraise_cancel=False, n=None, busy=False, step=1):
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
    if n is None:
        n = len(xs)

    n /= step

    if not progress and use_progress and n > threshold:
        progress = open_progress(n, busy=busy)

    def gen():
        if use_progress and (n > threshold or progress):

            for i, x in enumerate(xs):
                if progress.canceled:
                    raise CancelLoadingError
                elif progress.accepted:
                    break

                prog = None if i % step else progress

                r = func(x, prog, i, n)
                if r:
                    if hasattr(r, '__iter__'):
                        for ri in r:
                            yield ri
                    else:
                        yield r
        else:
            for x in xs:
                r = func(x, None, 0, 0)
                if r:
                    if hasattr(r, '__iter__'):
                        for ri in r:
                            yield ri
                    else:
                        yield r

    try:
        items = list(gen())
        if progress:
            progress.close()

        return items
    except CancelLoadingError:
        if reraise_cancel:
            if progress:
                progress.close()

            raise CancelLoadingError
        else:
            if progress:
                progress.close()

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
            if prog:
                prog.close()
        else:
            for i, x in enumerate(xs):
                func(x, None, i, n)

    try:
        gen(progress)
    except CancelLoadingError:
        if reraise_cancel:
            raise CancelLoadingError

# ============= EOF =============================================
