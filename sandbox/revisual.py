import time

from pylab import *
import hglib


p = '/Users/ross/Programming/mercurial/pychron_dev/'
repo = hglib.open(p)
x, y = [], []
for l in repo.log():
    i, rev, _, br, name, note, t = l
    x.append(time.mktime(t.timetuple()))
    y.append(float(i))

##plot(x[:200], y[:200])
x = array(x)
#y=array(y[::-1])
#
x -= x[-1]
##x=x[:-1]
x /= (3600. * 24)
#
#
#x=x[-200:]
#y=y[-200:]
#
#
#t=0
#nx=[]
#ny=[]
#for yi,di in zip(y,diff(x)):
#    for j in xrange(int(ceil(di))):
#        print t, yi
#        nx.append(t)
#        ny.append(yi)
#        t+=1

#print gradient(y[:-1], x)
#print diff(x)
#print y
#y=smooth(y, window_len=3)
#print y
#plot(nx, gradient(ny))
#plot(nx,ny)
#plot(nx[:-1], diff(ny))
#plot(nx,convolve(ny, [-1,0,0,0,0,1], mode='same'))
#plot(x[:-1], gradient(y[:-1], diff(x)))
#plot(x[:-1], diff(y)/diff(x))
p = polyfit(x, y, 2)
dx = max(x) - min(x)
fx = linspace(min(x), max(x), dx + 1)
fy = polyval(p, fx)
subplot('211')
plot(x, y)
fig = gcf()
fig.axes[0].xaxis.set_visible(False)
#a.set_

plot(fx, fy)

subplot('212')
#plot(fx, convolve(fy, [-1,0,-1], mode='same'))
plot(fx, gradient(fy))
xlabel('days')
ylabel('Changes/Day')

subplots_adjust(hspace=0.001)
show()





