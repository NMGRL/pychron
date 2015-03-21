# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
import difflib
# ============= standard library imports ========================
# ============= local library imports  ==========================

# def extract_line_changes(a, b):
#     diff_iter =difflib.context_diff(a,b)
#     diff_iter=difflib.unified_diff(a,b)
#     for di in diff_iter:
#         print di.strip()
#
#     diff_iter =difflib.ndiff(a,b)
#     llineno=0
#     rlineno=0
#     ls,rs=[],[]
#     is_add=False
#
#     p=''
#     for i,di in enumerate(diff_iter):
#         # print i, di.rstrip()
#         if not di.strip():
#             llineno+=1
#             rlineno+=1
#         elif di[0]=='-':
#             if not di[1:].strip():
#                 llineno+=1
#             elif p[0]==' ' and p.strip():
#                 rs.append(llineno)
#             ls.append(llineno)
#         elif di[0]=='+':
#             if not di[1:].strip():
#                 rlineno+=1
#                 continue
#             elif p[0]==' ' and p.strip():
#                 print 'append ls', rlineno
#                 ls.append(rlineno)
#             print 'append rs', rlineno
#             rs.append(rlineno)
#
#         p=di
#
#     return list(set(ls)), list(set(rs))

def extract_bounds(line):
    """
        @@ -1,4 +1,4 @@
    """
    args = line.split('@@')
    line = args[1]

    a, b = line.strip().split(' ')

    sa, ea = a.split(',')
    sb, eb = b.split(',')

    bnds = (sa[1:], ea, sb, eb)
    a,b,c,d = map(lambda x: int(x), bnds)
    print line
    return a,b,c,d

    # return (int(sa[1:]), int(ea)), (int(sb), int(eb))

def extract_line_numbers(a, b):
    # diff_iter = difflib.unified_diff(a.split('\n'), b.split('\n'))
    diff_iter = difflib.ndiff(a.split('\n'), b.split('\n'))
    ls, rs = [], []
    llineno,rlineno=0,0
    print '-----------------------'
    for di in diff_iter:
        di=str(di).rstrip()
        if di:
            d0=di[0]
            if d0=='-':
                ls.append(llineno)
                llineno+=1
            elif d0=='+':
                rs.append(rlineno)
                rlineno+=1
            elif d0==' ':
                llineno+=1
                rlineno+=1
            elif d0=='?':
                pass
                # if '+' in di:
                #     rs.append(float(llineno))
                # else:
                #     ls.append(float(rlineno))
        else:
            llineno+=1
            rlineno+=1
        print di.rstrip()

    return ls, rs

def extract_line_changes(a, b):
    diff_iter = difflib.unified_diff(a.split('\n'), b.split('\n'))
    ls, rs = [], []
    for di in diff_iter:
        print di.rstrip()
        if di.startswith('@@'):
            s1, e1, s2, e2 = extract_bounds(di)
            ls.append((s1, e1))
            rs.append((s2, e2))

    return ls, rs


if __name__ == '__main__':
    a = '''a=1
b=1
c=1
d=1'''
    b = '''a=12
b=1'''
    print extract_line_numbers(a,b)
# ============= EOF =============================================



