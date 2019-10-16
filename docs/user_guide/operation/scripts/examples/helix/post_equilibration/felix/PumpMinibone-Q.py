def main():
	if get_resource_value(name='FelixMiniboneFlag'):
		info('Pump minibone')
		open(description='Bone to Minibone')
		open(description='Minibone to Turbo')
		
		#open(description='Quad Inlet')
		
		close(description='Minibone to Bone')
		set_resource(name='MinibonePumpTimeFlag',value=30)
		release('FelixMiniboneFlag')