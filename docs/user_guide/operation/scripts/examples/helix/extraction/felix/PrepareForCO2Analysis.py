'''
mass spec equivalent
Message "Preparing for CO2 Analysis"
Close "Mass Spec Inlet"
Open "MS Ion Pump"
Close "Bone to Minibone"
Open "Bone to Turbo"
Open "Bone to Getter GP-50"
Close "Bone to Diode Laser"
Close "CO2 Laser to Jan"
Open "CO2 Laser to Felix"
Open "Bone to CO2 Laser"
'''
def main():
	info('Preparing for CO2 Analysis')
	close(description='Felix Inlet')
	open(description='Felix Ion Pump')
	close(description='Bone to Minibone')
	open(description='Bone to Turbo')
	open(description='Bone to Getter GP-50')
	close(description='Bone to Diode Laser')
	close(description='CO2 Laser to Jan')
	open(description='CO2 Laser to Bone')
	open(description='Bone to CO2 Laser')