# ===============================================================================
# Copyright 2015 Jake Ross
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


def confirmation_dialog(msg, return_retval=False,
                        cancel=False, title='',
                        timeout=None, size=None,
                        timeout_ret=None, **kw):
    if size is None:
        size = (-1, -1)
    from pychron.core.ui.dialogs import myConfirmationDialog

    dlg = myConfirmationDialog(
        cancel=cancel,
        message=msg,
        title=title,
        style='modal',
        size=size, **kw)

    if timeout_ret is not None:
        dlg.timeout_return_code = timeout_ret

    # print dlg
    retval = dlg.open(timeout)
    from pyface.api import YES, OK

    if return_retval:
        return retval
    else:

        return retval in (YES, OK)


def remember_confirmation_dialog(msg,
                                 title='',
                                 size=None,
                                 **kw):
    if size is None:
        size = (-1, -1)

    from pychron.core.ui.dialogs import RememberConfirmationDialog

    dlg = RememberConfirmationDialog(
        # cancel=cancel,
        message=msg,
        title=title,
        style='modal',
        size=size, **kw)

    # if timeout_ret is not None:
    #     dlg.timeout_return_code = timeout_ret

    retval = dlg.open()
    from pyface.api import YES, OK

    return retval in (YES, OK), dlg.remember
# ============= EOF =============================================
