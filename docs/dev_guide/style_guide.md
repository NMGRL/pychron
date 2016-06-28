Style Guide
=================

- Follow pep8. 
- use 4 spaces
- max line length 120
- method/functions all lowercase

```python
def foobar():
```

- classes PascalCase

```python
class FooBar:
```

- variables should be all lowercase

```python
x = 10
xmax = 102
x_min =0
```

- global variables all UPPERCASE

```python
DEBUG = True
```

- use single quotes for strings

```python
msg = 'Hello world'
```

- use triple double quotes for doc strings

```
def foobar():
    """
    this is a docstring
    """
```

- import individual items from numpy

```
from numpy import array
```

DO NOT USE

```
import numpy as np
```


- multiline list, dict, tuples

```
x = [1,2,3,
     4,5,6]
     
d = {'a': 1,
     'b': 2}
     
t= (1,2,
    3,4)
```

Pycharm Template
----------------

Use this template for new files. Pycharm templates are located in Preferences>Editor>File and Code Templates. 
note for Windows, Preferences are referred to as Settings


```python
# ===============================================================================
# Copyright ${YEAR} ${USER}
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

# ============= standard library imports ========================
# ============= local library imports  ==========================


# ============= EOF =============================================
```
