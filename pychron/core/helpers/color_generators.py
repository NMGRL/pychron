# ===============================================================================
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
# ===============================================================================



'''
Color generator methods
utility functions for creating a series of colors
'''

colors8i = dict(
    black=(0, 0, 0),
    red=(255, 0, 0),
    maroon=(127, 0, 0),
    yellow=(255, 255, 0),
    olive=(127, 127, 0),
    limegreen=(0, 255, 0),
    green=(0, 127, 0),
    gray=(127, 127, 127),
    aquamarine=(0, 255, 255),
    teal=(0, 127, 127),
    blue=(0, 0, 255),
    silver=(191, 191, 191),
    navy=(0, 0, 127),
    plum=(255, 0, 255),
    purple=(127, 0, 127),
    blueviolet=(159, 95, 159),
    brown=(165, 42, 42),
    firebrick=(142, 35, 35),
    greenyellow=(147, 219, 112),
    white=(255, 255, 255),
    darkgreen=(32, 117, 49)

)

colors1f = dict()
for color in colors8i:
    c = colors8i[color]
    colors1f[color] = c[0] / 255., c[1] / 255., c[2] / 255.

colornames = ['black', 'limegreen', 'blue', 'violet', 'maroon',
              'red', 'gray', 'green', 'aquamarine',
              'silver', 'navy', 'plum', 'purple',
              'blue violet', 'brown', 'firebrick', 'greenyellow',
              ]

allcolornames = ['aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure',
                 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood',

                 'cadetblue', 'chartreuse', 'chocolate', 'clear', 'coral', 'cornflowerblue',
                 'cornsilk', 'crimson', 'cyan',

                 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkgrey', 'darkkhaki',
                 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen',
                 'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise', 'darkviolet', 'deeppink',
                 'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue',

                 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia',
                 'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'grey',
                 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory', 'khaki',

                 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan',
                 'lightgoldenrodyellow', 'lightgray', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon',
                 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightslategrey', 'lightsteelblue',
                 'lightyellow', 'lime', 'limegreen', 'linen',

                 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple',
                 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred',
                 'midnightblue', 'mintcream', 'mistyrose', 'moccasin',

                 'navajowhite', 'navy', 'none', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid',

                 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff',
                 'peru', 'pink', 'plum', 'powderblue', 'purple',

                 'red', 'rosybrown', 'royalblue',

                 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue',
                 'slateblue', 'slategray', 'slategrey', 'snow', 'springgreen', 'steelblue', 'sys_window',

                 'tan', 'teal', 'thistle', 'tomato', 'transparent', 'turquoise', 'violet', 'wheat',
                 'white', 'whitesmoke', 'yellow', 'yellowgreen']

colorname_pairs = [
    (0xffbf33, 0x2b46d6),
    (0x00ffff, 0xff5300),
    (0xff00ff, 0xebff00),
    (0x00cc66, 0xff2c00),
    (0x0021cc, 0xffaf00),
    (0xffe200, 0x4d00cc),
    (0xdff400, 0xcc00c8),
    (0x5adb00, 0xe40034),
    # (0xFF5300, 0x00ffff),
    # (0x0000cc, 0xffbd00),
]


def compare_colors(cv, r, g, b):
    nc = int('{:02x}{:02x}{:02x}'.format(r, g, b), 16)
    return cv == nc


def gen(cnames):
    i = 0
    while 1:
        if i == len(cnames):
            i = 0
        yield cnames[i]
        i += 1


def paired_colorname_generator():
    return gen(colorname_pairs)


def colorname_generator():
    """
    """
    return gen(colornames)


def color8i_generator():
    """
    """
    i = 0
    while 1:
        if i > len(colornames):
            i = 0
        yield colors8i[colornames[i]]
        i += 1


def color1f_generator():
    """
    """
    i = 0
    while 1:
        if i > len(colornames):
            i = 0
        yield colors1f[colornames[i]]
        i += 1
