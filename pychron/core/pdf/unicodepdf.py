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
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

c = Canvas('/Users/ross/Desktop/temp.pdf', pagesize=(200,100))
c.setPageCompression(0)
y = 50

line = 'fooobasd \xb1 \xb2 \xf3'

pdfmetrics.registerFont(TTFont('Arial', '/Library/Fonts/Microsoft/Arial.ttf'))
pdfmetrics.registerFontFamily('Arial', normal='Arial')
c.setFont('Arial', 20)
c.drawString(50, y, line.strip())

c.save()
# ============ EOF =============================================
