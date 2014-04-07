class CRCError(BaseException):
    _cmd = ''

    def __init__(self, cmd):
        self._cmd = cmd

    def __str__(self):
        return self._cmd
