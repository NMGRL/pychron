# # ===============================================================================
# # Copyright 2011 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
#
#
# # =============enthought library imports=======================
# # ============= standard library imports ========================
# # ============= local library imports  ==========================
#
# # def code_generator(grp, start=0, step=1):
# #    i = start
# #    while 1:
# #        yield '{}{:02n}'.format(grp, i)
# #        i += step
# #
# #
# # def get_code_decorator(code_gen):
# #    def decorator(cls):
# #        if cls.code is None:
# #            cls.code = code_gen.next()
# #        return cls
# #    return decorator
#
#
# class ErrorCode:
#     msg = ''
#     code = None
#     description = ''
#
#     def __str__(self):
#         return 'ERROR {} : {}'.format(self.code, self.msg)
#
#
# # class InvalidDirectoryErrorCode(ErrorCode):
# #    msg1 = 'directory {} does not exist'
# #    msg2 = '{} is not a directory {}'
# #    code = '900'
# #    def __init__(self, name, style=1, *args, **kw):
# #        if style == 1:
# #            self.msg = self.msg1.format(name)
# #        else:
# #            self.msg = self.msg2.format(name)
#
# # ============= EOF =====================================
