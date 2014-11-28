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



#============= enthought library imports =======================

#============= standard library imports ========================
import os
import time
import subprocess
#============= local library imports  ==========================

def write_stats(stats):
    '''
    '''

    f = open(os.path.join(root, 'stats.txt'), 'a')

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    f.write('====== %s ======\n' % timestamp)
    f.write('%s\n' % stats)
    f.close()


def scan(root):
    '''
    
    '''
    with open(os.path.join(root, 'sloccount_stats.txt'), 'w') as f:
        os.environ['PATH'] = ':'.join((os.environ['PATH'], '/usr/local/bin'))
        subprocess.call(['/usr/local/bin/sloccount', root, 'cached'],
                        stdout=f
        )
        # parse results
    with open(os.path.join(root, 'sloccount_stats.txt'), 'r') as f:
        line = f.next().strip()
        while line != 'Computing results.':
            line = f.next().strip()

        # parse individual packages


        while line != 'Totals grouped by language (dominant language first):':
            line = f.next().strip()

        line = f.next().strip()
        while line:
            # parse individual languages
            lang, stats = line.split(':')
            n, per = stats.strip().split(' ')
            n = int(n)
            per = float(per[1:-2])

            print lang, n, per
            line = f.next().strip()


def plot_stats(root):
    '''
    '''
    from pylab import plot, show, date2num, subplot
    from datetime import datetime

    with open(os.path.join(root, 'stats.txt')) as f:
        lines = f.read().split('\n')
        lines = [l for l in lines if l.rstrip()]
        start_t = None
        x = []
        y1 = []
        y2 = []
        y3 = []
        for i in range(0, len(lines), 4):
            tstamp = lines[i].split('= ')[1].split(' =')[0]
            t = date2num(datetime.strptime(tstamp, '%Y-%m-%d %H:%M:%S'))
            if start_t is None:
                start_t = t
                t = 0
            else:
                t -= start_t

            if i + 1 < len(lines):
                nfile = int(lines[i + 1].split(':')[1])
                nlines = int(lines[i + 2].split(':')[1])
                tlines = int(lines[i + 3].split(':')[1])
                x.append(t)
                y1.append(nfile)
                y2.append(nlines)
                y3.append(tlines)

    subplot('311')
    plot(x, y1, 'r')
    subplot('312')
    plot(x, y2, 'g')
    subplot('313')
    plot(x, y3, 'b')
    show()


if __name__ == '__main__':
    root = os.getcwd()
    scan(root)
    # plot_stats(root)
#============= EOF ====================================
# def get_num_lines(file):
#    '''
#    '''
#    comment = False
#    cnt = 0
#    tcnt = 0
#    for line in open(file, 'r'):
#        tcnt += 1
#        line = line.strip()
#
#        if line.startswith("'''"):
#            comment = not comment
#
#        if comment:
#            continue
#        if line.startswith('#'):
#            continue
#
#        if len(line) > 0:
#            cnt += 1
#    return tcnt, cnt
#
#    print 'scanning %s' % root
#    totlines = 0
#    totfiles = 0
#    totclines = 0
#    for root, _dirs, files in os.walk(root):
#        for file in files:
#            if not file.startswith('.'):
#                if file.endswith('.py'):
#                    if file != '__init__.py':
#                        file = os.path.join(root, file)
#
#                        alines, clines = get_num_lines(file)
#                        #print file,lines
#                        totfiles += 1
#                        totclines += clines
#                        totlines += alines
#    stats = 'number files: %i\nnumber lines code: %i\nnumber total lines: %i' % (totfiles, totclines, totlines)
#    print stats
#    write_stats(stats)
