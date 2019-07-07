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
import re
WISCAR_DET_RE = re.compile(r'^S\d\d\d(?P<detector>[A-Za-z]{2}\d)-')
WISCAR_ID_RE = re.compile(r'^[A-Z]{3}[0-9]{4}$', re.IGNORECASE)

# ============= EOF =============================================
