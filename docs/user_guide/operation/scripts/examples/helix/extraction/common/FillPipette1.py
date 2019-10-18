'''
'''
def main():
	info('Fill Pipette 1')
	close(description='Outer Pipette 1')
	sleep(1)
	if analysis_type=='blank':
		info('not filling cocktail pipette')
	else:
		info('filling cocktail pipette')
		open(description='Inner Pipette 1')
		
	sleep(15)
	close(description='Inner Pipette 1')
	sleep(1)