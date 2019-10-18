'''
eqtime: 15
'''
def main():
    """
    The CO2 whiff script is the same as a normal co2 extraction script
    !except! for the last step

    instead of equilibrating with the mass spec back to the co2 chamber
    the chamber is isolated. If the whiff action is "run remainder" than
    equilibrate with the chamber
    """
    info('Jan CO2 laser analysis')
    gosub('jan:WaitForCO2Access')
    gosub('jan:PrepareForCO2Analysis')

    gosub('jan:CO2Analysis')

    # isolate chamber
    info('Isolating CO2 chamber for whiffing')
    close('T')    
