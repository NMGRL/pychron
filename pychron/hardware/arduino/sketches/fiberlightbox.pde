/*
  Copyright 2011 Jake Ross

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

//version 0.2


#include <Streaming.h>
#include <CmdMessenger.h>

CmdMessenger cmdMessenger=CmdMessenger(Serial,',',';');

enum{
  kCOMM_ERROR = 000, // Lets Arduino report serial port comm error back to the PC (only works for some comm errors)
  kACK = 001, // Arduino acknowledges cmd was received
  kARDUINO_READY = 002, // After opening the comm port, send this cmd 02 from PC to check arduino is ready
  kERR = 003, // Arduino reports badly formatted cmd, or cmd not recognised
  kSEND_CMDS_END,
};

// Commands we send from the PC and want to recieve on the Arduino.
// We must define a callback function in our Arduino program for each entry in the list below vv.
// They start at the address kSEND_CMDS_END defined ^^ above as 004
messengerCallbackFunction messengerCallbacks[] =
{
  on_callback, // 004 
  off_callback, // 005
  intensity_callback, // 006
  get_intensity_callback, //007
  get_state_callback, //008
  get_version_callback,//009
  NULL
};

byte remote_power_pin=9;
byte intensity_pin=11;

byte state=0;
char * intensity_buf;
char __version__[20]="0.2";
//================ Callbacks =============
void ready()
{
  cmdMessenger.sendCmd(kACK,"ready");
}
void unknownCmd()
{
  cmdMessenger.sendCmd(kERR,"unknown command");
}
void get_intensity_callback()
{
  cmdMessenger.sendCmd(kACK,intensity_buf);
}
void get_version_callback()
{
  cmdMessenger.sendCmd(kACK,__version__);
}
void get_state_callback()
{
  char buf[20];
  itoa(state,buf,10);
  cmdMessenger.sendCmd(kACK,buf);
}
void off_callback()
{ 
  digitalWrite(remote_power_pin, HIGH);
  cmdMessenger.sendCmd(kACK,"off");
  state=0;

}
void on_callback()
{

  digitalWrite(remote_power_pin, LOW);
  cmdMessenger.sendCmd(kACK,"on");
  state=1;
  
}
void intensity_callback()
{

  if (!cmdMessenger.available())
    cmdMessenger.sendCmd(kERR,"no channel set");

  while(cmdMessenger.available())
  {
    char buf[350] = {
      '\0'    };
    cmdMessenger.copyString(buf,350);
    if(buf[0])
    {
      int v=atoi(buf);
      intensity_buf= buf;
      analogWrite(intensity_pin,v);
      cmdMessenger.sendCmd(kACK,"intensity");
    }
  }

}

//================ Setup =================

void attach_callbacks(messengerCallbackFunction* callbacks)
{
  int i = 0;
  int offset = kSEND_CMDS_END;
  while(callbacks[i])
  {
    cmdMessenger.attach(offset+i, callbacks[i]);
    i++;
  }
}
void setup()
{
  Serial.begin(115200);
  cmdMessenger.print_LF_CR(); // Make output more readable whilst debugging in Arduino Serial Monitor
  cmdMessenger.attach(kARDUINO_READY,ready);
  cmdMessenger.attach(unknownCmd);
  pinMode(remote_power_pin,OUTPUT);
  pinMode(intensity_pin,OUTPUT);
  attach_callbacks(messengerCallbacks);
}
void loop()
{
  cmdMessenger.feedinSerialData();

}

