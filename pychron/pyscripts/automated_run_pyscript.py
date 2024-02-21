from pychron.pyscripts.valve_pyscript import ValvePyScript


class AutomatedRunPyScript(ValvePyScript):
    automated_run = None

    def _automated_run_call(self, func, *args, **kw):
        if self.automated_run is None:
            return

        if isinstance(func, str):
            func = getattr(self.automated_run, func)

        return func(*args, **kw)
