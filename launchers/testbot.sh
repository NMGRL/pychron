#!/bin/bash
mline="==================================================================================="
marea="+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo $mline
echo Starting Test Bot
echo $mline
echo
 
echo Testing Launch system
echo
echo $marea
src_dir=~/Programming/mercurial/pychron_test
testbot_dir=~/Programming/testbot

python $src_dir/launchers/test.py
echo $marea
echo

if pgrep -f remote_hardware_server.py
then
	echo Remote Server running
else
	echo Launching RemoteHardwareServer...
	python $src_dir/launchers/remote_hardware_server.py &
fi
echo

if pgrep -f pychron.py
then
	echo Pychron Running
else
	echo Launching Pychron...
	echo Using Pychrondata_test and pychron_test
 
	python $src_dir/launchers/pychron.py &
fi
# if pgrep -f emulator.py
# then
# 	echo Pychron emulator is running
# else
# 	echo launching Pychron emulator
# 	python $src_dir/launchers/emulator.py &
# 	echo Waiting 30 secs for pychron launch and tests
# 	sleep 5
# 	echo Waking Testbot
# fi
# 
# if pgrep -f MassSpec_testbot.app 
# then
# 	echo MassSpec_testbot is running
# else
# 	echo Launching MassSpec_testbot
# 	open $testbot_dir/MassSpec_testbot.app &
# 	echo Waiting 20 secs for pychron launch and tests
# 	sleep 20
# 	echo Waking MassSpec
# fi
# 
# echo Triggering testbot applescript
# osascript $testbot_dir/massspec_testbot_script &
# 
# 
# sleep 20
# kill $(pgrep -f MassSpec_testbot.app)
# echo Finished
