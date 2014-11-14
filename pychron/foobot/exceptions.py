class InvalidSyntax(BaseException):
    pass


class InvalidFunction(BaseException):
    def __init__(self, name, valid):
        super(InvalidFunction, self).__init__()
        self.valid = valid
        self.name = name


class InvalidExperiment(BaseException):
    def __init__(self, name):
        self.name = name


class InvalidScript(BaseException):
    pass
    # def __init__(self, name):
    # self.name = name
