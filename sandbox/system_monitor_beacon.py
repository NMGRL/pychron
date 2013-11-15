"""
 test script that periodically
 sends random messages using zmq.Publisher patterb
"""
import random
import time
import sys
import os
from traits.etsconfig.etsconfig import ETSConfig

ETSConfig.toolkit = 'qt4'

d = os.path.dirname(os.getcwd())
sys.path.append(d)
#print sys.path
from pychron.messaging.notify.notifier import Notifier


def beacon(port):
    colors = ['red', 'green', 'blue', 'orange']
    n = Notifier()
    n.setup(port)
    for i in xrange(100000):
        color = random.choice(colors)
        msg = '{}|beacon number {}, {}'.format(color, i, random.random())
        print 'Sending message {}'.format(msg)
        n.send_console_message(msg)
        time.sleep(1.5)


if __name__ == '__main__':
    beacon(8100)


