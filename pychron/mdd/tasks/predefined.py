# ===============================================================================
# Copyright 2018 ross
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


# ============= MDD =============================================
LABTABLE = """
required:
nodes:
  - klass: UnknownNode
  - klass: GroupingNode
  - klass: MDDLabTableNode
  - klass: FilesNode

"""
FILES = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: FilesNode
"""

ARRME = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: ArrMeNode
"""

AUTOARR = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: AutoArrNode
"""

ARRMULTI = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: ArrMultiNode
"""

MDDFIGURE = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: MDDFigureNode
"""

AGESME = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: AgesMeNode
"""

AUTOAGEFREE = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: AutoAgeFreeNode
"""

AUTOAGEMON = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: AutoAgeMonNode
"""

CORRFFT = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: CorrFFT
"""

CONFINT = """
required:
nodes:
  - klass: MDDWorkspaceNode
  - klass: ConfInt
"""
# ============= EOF =============================================
