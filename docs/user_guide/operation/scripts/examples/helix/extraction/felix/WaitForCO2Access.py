def main():
    info('Waiting for CO2 access')
    wait('JanCO2Flag', 0)
    info('CO2 free')
    wait('CO2PumpTimeFlag', 0)
    acquire('FelixCO2Flag', clear=True)
    info('CO2 acquired')
    
    
    