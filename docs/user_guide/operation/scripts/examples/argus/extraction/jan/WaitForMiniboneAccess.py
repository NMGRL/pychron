def main():
    info('Waiting for minibone access')
    wait('FelixMiniboneFlag', 0)
    info('Minibone free')
    acquire('JanMiniboneFlag', clear=True)
    info('Minibone acquired')
    wait('MinibonePumpTimeFlag', 0)
    
    