'''
'''
N=1000
VALVE='W'
def main():
    info("Actuate {} a bunch of times".format(VALVE))
    
    for i in xrange(N):
        info('Iteration= {:03n}/{:03n}'.format(i,N))
        if i%2:
            close(VALVE)
        else:
            open(VALVE)
        sleep(1)
            
    close(VALVE)
