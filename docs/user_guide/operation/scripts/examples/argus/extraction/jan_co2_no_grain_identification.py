'''
eqtime: 12
'''
def main():
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')
    gosub('jan:CO2AnalysisNoGrainID')
