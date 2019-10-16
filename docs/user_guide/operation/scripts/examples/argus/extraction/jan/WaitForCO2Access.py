def main():
    info('Waiting for CO2 access')
    wait('FelixCO2Flag', 0)
    info('CO2 free')
    wait('CO2PumpTimeFlag', 0)
    acquire('JanCO2Flag', clear=True)
    info('CO2 acquired')
    
    
    