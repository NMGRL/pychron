from pylab import *

import os
def plot_mem(p, use_histogram=True):
    with open(p, 'r') as fp:
        ms = []
        started = False
        mx, mn = -Inf, Inf
        for line in fp:

            # print line
            msg, mem = map(str.strip, line.split(':'))
            x = float(mem)
            mn = min(mn, x)
            mx = max(mx, x)
#             print msg, mem
            if not started and msg.startswith('<'):
                started = True
                s = x
            elif started and msg.startswith('>'):
                started = False
                ms.append(x - s)

        if use_histogram:
            hist(ms, 30)
        else:
            plot(range(len(ms)), ms)


        print mn, mx, len(ms), (mx - mn) / float(len(ms))

#             try:
#                 yi = float(mem)
#                 continue
#             except ValueError:
#                 continue



def plot_file(p, normalize=False, stacked=False,
              use_gradient=False, memory=False):

    x = []
    y = []
    ts = []
    cnt = 0
    n = 0
    mi = Inf
    ma = -Inf
    if memory:
        subplot(2, 1, 1)

    mxs = []
    mys = []
    with open(p, 'r') as fp:
        xi = 0
        ticked = False
#         for line in fp:
#             msg, mem = map(str.strip, line.split(':'))
#             if msg.startswith('exp start'):
#                 break

        for line in fp:

            # print line
            msg, mem = map(str.strip, line.split(':'))
#             print msg, mem
#             if msg.startswith('exp start'):
#                 continue

#            if msg.startswith('collect'):
#                continue
            try:
                yi = float(mem)
                y.append(yi)
                x.append(xi)
                mi = min(mi, yi)
                ma = max(ma, yi)
                xi += 1
                ts.append(msg)

            except ValueError:
                continue

            if msg.startswith('>'):
                n += 1
                if not ticked and stacked:
                    xticks(x, ts, rotation=-90)
                    ticked = True
                    start_mem = y[0]

                y = array(y)
                end_mem = y[-1]

                mxs.append(cnt)
                mys.append((max(y) - min(y)))
                if normalize:
                    y -= y[0]

                if use_gradient:
                    x = x[1:]
                    y = diff(y)
#                     y = gradient(y)

                plot(x, y, label=os.path.basename(p) + str(cnt))
                if stacked:
                    xi = 0
                x = []
                y = []
                ts = []
                cnt += 1

        if len(x) > 1:
            end_mem = y[-1]
            n += 1
            y = array(y)
            if normalize:
                y -= y[0]

            if use_gradient:
                y = diff(y)
                x = x[1:]
#                 y = gradient(y)

            if not ticked and stacked:
                xticks(x, ts, rotation=-90)
            plot(x, y, label=os.path.basename(p) + str(cnt))

        if memory:
            subplot(2, 1, 2)
            print mxs
            plot(mxs, mys)

        print 'Min: {}  Max: {} avg: {} n: {}'.format(mi, ma, (ma - mi) / float(n), n)
#         print 'start: {} end: {}'.format(start_mem, end_mem)
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n,--normalize', dest='normalize',
                        action='store_const',
                        const=bool,
                        default=False)
    parser.add_argument('-s,--stacked', dest='stacked',
                        action='store_const',
                        const=bool,
                        default=False)
    parser.add_argument('-g,--gradient', dest='gradient',
                        action='store_const',
                        const=bool,
                        default=False)
    parser.add_argument('-m,', dest='memory',
                        action='store_const',
                        const=bool,
                        default=False)
    parser.add_argument('-u,', dest='usize',
                        action='store_const',
                        const=bool,
                        default=False)

    parser.add_argument('-U,', dest='uhist',
                        action='store_const',
                        const=bool,
                        default=False)

    parser.add_argument('paths', metavar='p', nargs='+')
    args = parser.parse_args()
    print args

    root = os.path.expanduser('~')
    d = os.path.join(root, 'Desktop', 'memtest')
    if args:
        paths = args.paths
        normalize = args.normalize
        stacked = args.stacked
        grad = args.gradient
        mem = args.memory
        usize = args.usize
        uhist = args.uhist

        if paths[0] == 'last':
            i = 1
            while 1:
                pa = os.path.join(d, 'mem-{:03n}.txt'.format(i))
                if os.path.isfile(pa):
                    i += 1
                else:
                    pa = os.path.join(d, 'mem-{:03n}.txt'.format(i - 1))
                    if os.path.isfile(pa):
                        break
                    else:
                        i += 1

            if usize:
                plot_mem(pa, use_histogram=False)
            elif uhist:
                plot_mem(pa, use_histogram=True)
            else:
                plot_file(pa, normalize=normalize,
                      stacked=stacked,
                      use_gradient=grad,
                      memory=mem
                      )
            tight_layout()
            show()

        else:
            for ai in paths:
                n = 'mem-{:03n}.txt'.format(int(ai))
                p = os.path.join(d, n)
                plot_file(p, normalize=normalize, stacked=stacked, use_gradient=grad,)
#                legend(loc='upper left')
                tight_layout()
                show()
