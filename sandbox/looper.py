import time
from threading import Thread
import os
import psutil
from pychron.consumer_mixin import consumable
import gc
PID = os.getpid()

def get_mem():
    proc = psutil.Process(PID)
    mem = proc.get_memory_info()
    return mem.rss / 1024.**2

def loop():
    i = 0
    n = 100


    print '{} '.format(get_mem())
    with consumable():
        print '{} '.format(get_mem())
        while 1:
            if i > n:
                break
            time.sleep(0.05)
            i += 1
            if not i % 10:
                print i

    print '{} '.format(get_mem())
def dloop():
    for i in range(4):
        loop()

def main():
    t = Thread(name='loop',
             target=dloop
             )
    t.start()
    t.join()




if __name__ == '__main__':
    main()
