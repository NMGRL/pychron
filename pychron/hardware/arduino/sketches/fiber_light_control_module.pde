#include <Messenger.h>

/*
Jake Ross
New Mexico Geochronology Research Laboratory 2010

remote operation of a fiber optic illuminator Model 21DC

used to light laser stage area
*/


/*
Communication protocal

<cmd> <id>

cmd 
  o,O=on
  f,F=off
id
  A...Z
 
<cmd> <value> 
cmd 
  i,I=intensity
value
  0-255


*/
Messenger message = Messenger();
byte remote_power_pin = 9;
byte intensity_pin = 11;

void setup()
{
  Serial.begin(9600);
  message.attach(handle_message);
  pinMode(remote_power_pin,OUTPUT);
  pinMode(intensity_pin,OUTPUT);
}

void loop()
{
  while(Serial.available()) message.process(Serial.read());
     
}
