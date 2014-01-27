#===============================================================================
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
#===============================================================================



def add_sub_error_prop(errors):
    error = reduce(lambda a, b: (a ** 2 + b ** 2) ** 0.5, errors)
    return error
def mult_div_error_prop(values, errors):
    error = reduce(lambda a, b:((a[1] / a[0]) ** 2 + (b[1] / b[0]) ** 2) ** 0.5 , zip(values, errors))
    return error
