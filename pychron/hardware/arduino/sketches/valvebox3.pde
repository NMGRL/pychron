/* 
 ---- basic communication example ----
 Control Arduino board functions with the following messages:
 
 r a -> read analog pins
 r d -> read digital pins
 w d [pin] [value] -> write digital pin
 w a [pin] [value] -> write analog pin
 p m [pin] [value] -> set pin mode
 
 
 Base: Thomas Ouellet Fredericks 
 Additions: Alexandre Quessy 
 
 */


#include <Messenger.h>


// Instantiate Messenger object with the message function and the default separator (the space character)
Messenger message = Messenger(); 

// Define messenger function
void messageCompleted() {
  if ( message.checkString("r") ) 
  { // Read pins (analog or digital)
      int pin;
      int i=message.readInt();
    
//      if ( message.checkString("io") ) 
//      {
//
//        i=message.readInt();
//        pin=i-1;
//      }
//      else if (message.checkString("ic"))
//      {
//        Serial.print("ic ");   
//        i=message.readInt();
//        pin=i-2;
//      }


      Serial.print(digitalRead(i), DEC);
      Serial.println(); // Terminate message  
  } 
  else if ( message.checkString("w") ) 
  { // Write pin (analog or digital)

      int pin = message.readInt();
      int state = message.readInt();
      digitalWrite(pin,state); //Sets the state of the pin 
            Serial.print("OK");
            Serial.println();
    } 
    else if ( message.checkString("p") &&  message.checkString("m") ) 
    { // Pin mode
      int pin = message.readInt();
      int mode = message.readInt();
      pinMode(pin,mode);
  }


}

void setup() {
  // Initiate Serial Communication
  
  pinMode(51,OUTPUT);
  pinMode(50,INPUT);
  pinMode(49,INPUT);
  
  pinMode(48,OUTPUT);
  pinMode(47,INPUT);
  pinMode(46,INPUT);  
  
  pinMode(45,OUTPUT);
  pinMode(44,INPUT);
  pinMode(43,INPUT);
  
  
  pinMode(42,OUTPUT);
  pinMode(41,INPUT);
  pinMode(40,INPUT);
  
  pinMode(39,OUTPUT);
  pinMode(38,INPUT);
  pinMode(37,INPUT);
  
  pinMode(36,OUTPUT);
  pinMode(35,INPUT);
  pinMode(34,INPUT);
  
  pinMode(33,OUTPUT);
  pinMode(32,INPUT);
  pinMode(31,INPUT);
  
  pinMode(30,OUTPUT);
  pinMode(29,INPUT);
  pinMode(28,INPUT);
  
  pinMode(27,OUTPUT);
  pinMode(26,INPUT);
  pinMode(25,INPUT);
  
  pinMode(24,OUTPUT);
  pinMode(23,INPUT);
  pinMode(22,INPUT);
  
  Serial.begin(115200); 
  message.attach(messageCompleted);
  
  
  
}

void loop() {
  // The following line is the most effective way of 
  // feeding the serial data to Messenger
  while ( Serial.available( ) ) message.process(Serial.read( ) );


}



