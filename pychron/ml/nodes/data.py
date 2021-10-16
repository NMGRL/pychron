# ===============================================================================
# Copyright 2020 ross
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
from pychron.core.helpers.strtools import get_case_insensitive, to_int
from pychron.pipeline.nodes import CSVNode


class CSVClusterNode(CSVNode):
    def _analysis_factory(self, d):
        from pychron.processing.analyses.file_analysis import FileAnalysis

        fa = FileAnalysis(
            age=float(get_case_insensitive(d, "age")),
            age_err=float(get_case_insensitive(d, "age_err")),
            kca=float(get_case_insensitive(d, "kca")),
            kca_err=float(get_case_insensitive(d, "kca_err")),
            record_id=get_case_insensitive(d, "runid"),
            sample=get_case_insensitive(d, "sample", ""),
            label_name=get_case_insensitive(d, "label_name", ""),
            group=to_int(get_case_insensitive(d, "group", "")),
            aliquot=to_int(get_case_insensitive(d, "aliquot", 0)),
        )
        return fa


# ============= EOF =============================================
