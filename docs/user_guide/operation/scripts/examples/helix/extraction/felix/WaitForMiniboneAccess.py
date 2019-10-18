def main():
    info('Waiting for minibone access')
    wait('JanMiniboneFlag', 0)
    info('Minibone released')
    wait('MinibonePumpTimeFlag', 0)
    acquire('FelixMiniboneFlag', clear=True)
    info('minibone acquired')
    
    
    