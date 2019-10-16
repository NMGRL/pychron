'''
modifier: 01
eqtime: 15
'''
def main():
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:WaitForMiniboneAccess')
    gosub('jan:PrepareForCO2_minibone_Analysis')
    gosub('jan:CO2Analysis')
