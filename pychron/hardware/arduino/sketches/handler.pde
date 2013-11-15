/*
Jake Ross
 New Mexico Geochronology Research Laboratory 2010
 
 remote operation of a fiber optic illuminator Model 21DC
 
 used to light laser stage area
 */

void handle_message()
{

  char cmd=message.readChar();
  Serial.Print(cmd);
  switch(cmd)
  {
    //on
  case 'o':
    digitalWrite(remote_power_pin,LOW);

    break;
  case 'O':
    digitalWrite(remote_power_pin,LOW); 
    break;
    //off
  case 'f':
    digitalWrite(remote_power_pin,HIGH);
    break;
  case 'F':
    digitalWrite(remote_power_pin,HIGH);
    break;
    //intensity
  case 'i':
    analogWrite(intensity_pin,message.readInt());
    break;
  case 'I':
    analogWrite(intensity_pin,message.readInt());
    break;

  }
  Serial.println("success");
  
}
