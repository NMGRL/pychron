
/* 
This is a test sketch for the Adafruit assembled Motor Shield for Arduino v2
It won't work with v1.x motor shields! Only for the v2's with built in PWM
control

For use with the Adafruit Motor Shield v2 
---->  http://www.adafruit.com/products/1438
*/


#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield(); 
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61); 

// Connect a stepper motor with 200 steps per revolution (1.8 degree)
// to motor port #1 (M1 and M2)
Adafruit_StepperMotor *motor = AFMS.getStepper(200, 1);

const int buttonPin = 2;    // the number of the pushbutton pin
const int ledPin = 13;      // the number of the LED pin

const int magnetPin = 7;
const int commsLedPin = 8;
const int forwardLedPin = 5;
const int reverseLedPin = 6;
const int reversePin = 3;
const int forwardPin = 2;
const int drivePin = 4;
const int magnetManualPin = 9;


// Variables will change:
int commsState = LOW;
int mode = 0;  // 0==software control 1==manual button control
int drive_state = 0;
int magnet_state = 0;

int nstep;
char buf[40]; 
int index=0;

void setup() {
  Serial.begin(9600);           // set up Serial library at 9600 bps
  
  AFMS.begin();  // create with the default frequency 1.6KHz
  TWBR = ((F_CPU /400000l) - 16) / 2; // Change the i2c clock to 400KHz
  
  //AFMS.begin(1000);  // OR with a different frequency, say 1KHz
  motor->setSpeed(50);  // 10 rpm   
  
  pinMode(magnetPin, OUTPUT);
  pinMode(commsLedPin, OUTPUT);
  pinMode(forwardLedPin, OUTPUT);
  pinMode(reverseLedPin, OUTPUT);

  pinMode(forwardPin, INPUT);
  pinMode(reversePin, INPUT);
  pinMode(drivePin, INPUT);
  pinMode(magnetManualPin, INPUT);

  digitalWrite(magnetPin, HIGH);
  digitalWrite(commsLedPin, HIGH);
  digitalWrite(forwardLedPin, LOW);
  digitalWrite(reverseLedPin, LOW);
  
}


void do_move(char* b){
      nstep = atoi(b);
      move(nstep);
}

void do_magnet(char* b){
// Serial.print(b);
 int state = atoi(b);
 set_magnet_state(state);
}
void do_rpm(char* b){
  int rpm = atoi(b);
  motor->setSpeed(rpm);
}
String do_status(){
  /* return status as a integer
   *  Bit 0 =  mode 0==software 1 manual
   *      1 =  moving 0 stop 1 in motion
   *      2 =  magnet 0 off 1 on
   */

   char buf[3];
   buf[2] = mode;
   buf[1] = drive_state;
   buf[0] = magnet_state;
   char *endp = NULL;
   return String(strtoul(buf, &endp, 2), HEX);
}

void serialEvent()
{
  /*
   * valid commands
   * g100 move 100 steps forward
   * g-100 move 100 steps backward
   * m0 magnets off
   * m1 magnets on
   */
  if (!mode){
    
      while(Serial.available())
      {
    //    digitalWrite(commsLedPin, LOW);
        char ch = Serial.read();
        Serial.print(ch);
        if(ch == '\n'){      
          String ret="invalid";
          char f = buf[0];
    
          char v[strlen(buf)];
          strncpy(v, buf+1, strlen(buf)); 
          ret = "OK";
          digitalWrite(commsLedPin, HIGH);
          switch (f){
            case 'g':
              do_move(v);
              break;
            case 'm':
              do_magnet(v);
              break;
            case 'r':
              do_rpm(v);
            break;
            case 's':
              ret = do_status();
              break;
            case 'e':
              motor->release();
            default:{
              ret="invalid";
            }
          }  
          Serial.println(ret);
          memset(buf, 0, sizeof(buf));
          index=0;      
        }else{
    //      Serial.print(commsState);
          delay(25);
          digitalWrite(commsLedPin, commsState);
          commsState =!commsState;
          buf[index++] = ch;
        }
        
      }
   }
   buf;
   index=0;
   digitalWrite(commsLedPin, HIGH);
}

void drive_mode(){
  mode = digitalRead(forwardPin)||digitalRead(reversePin);
  
}
void manual_drive(){
  if (mode && digitalRead(drivePin)){
    if (digitalRead(forwardPin)){
        digitalWrite(reverseLedPin, LOW);
        digitalWrite(forwardLedPin, HIGH);
        one_step(FORWARD);  
        digitalWrite(forwardLedPin, LOW);
      
    }else{
        digitalWrite(forwardLedPin, LOW);
        digitalWrite(reverseLedPin, HIGH);
        one_step(BACKWARD);
        digitalWrite(reverseLedPin, LOW);
      
    }
  }
}

void one_step(int dir){
  motor->onestep(dir, MICROSTEP);
}
void move(int nstep){
 if (nstep>0){
        digitalWrite(reverseLedPin, LOW);
        digitalWrite(forwardLedPin, HIGH);
        motor->step(nstep, FORWARD, SINGLE);
        digitalWrite(forwardLedPin, LOW);
      }else{
        digitalWrite(forwardLedPin, LOW);
        digitalWrite(reverseLedPin, HIGH);
        motor->step(-nstep, BACKWARD, SINGLE);  
        digitalWrite(reverseLedPin, LOW);
      }
}
void demo(){

  //digitalWrite(commsLedPin, LOW);
  digitalWrite(magnetPin, LOW);
  digitalWrite(forwardLedPin, LOW);
  digitalWrite(reverseLedPin, HIGH);
  move(100);
  
  delay(1000);
  digitalWrite(magnetPin, HIGH);
  digitalWrite(forwardLedPin, HIGH);
  digitalWrite(reverseLedPin, LOW);
  move(-100);
  //digitalWrite(commsLedPin, HIGH);
  delay(1000);

}
void set_magnet_state(int v){
  digitalWrite(magnetPin, !v);
  magnet_state = v;
}
void actuate(){
  if (mode && digitalRead(magnetManualPin)){
    set_magnet_state(HIGH);
  }else{
    set_magnet_state(LOW);
  }
}


void loop() {
  //Serial.print("mode");
//  Serial.print(digitalRead(forwardPin));
//  Serial.print(digitalRead(reversePin));
//  Serial.println(digitalRead(drivePin));
//  delay(50);
  drive_mode();
  manual_drive();
  actuate();
//   demo();
}



// EOF

//int is_drive_active()
//{
//  
//  int reading = digitalRead(drivePin);
//
//  // check to see if you just pressed the button
//  // (i.e. the input went from LOW to HIGH), and you've waited long enough
//  // since the last press to ignore any noise:
//
//  // If the switch changed, due to noise or pressing:
//  if (reading != lastButtonState) {
//    // reset the debouncing timer
//    lastDebounceTime = millis();
//  }
//
//  if ((millis() - lastDebounceTime) > debounceDelay) {
//    // whatever the reading is at, it's been there for longer than the debounce
//    // delay, so take it as the actual current state:
//
//    // if the button state has changed:
//    if (reading != buttonState) {
//       drive_active = reading;
//       
//      buttonState = reading;
//      // only toggle the LED if the new button state is HIGH
////      if (buttonState == HIGH) {
////        ledState = !ledState;
//        // set the LED:
////        digitalWrite(ledPin, HIGH);
//        
////        if (ledState) {motor->step(350, FORWARD, DOUBLE);}
////        else {motor->step(350, BACKWARD, DOUBLE);}
////        }
////        digitalWrite(ledPin, LOW);
//     
//      }
//    }
//
//    // save the reading. Next time through the loop, it'll be the lastButtonState:
//  lastButtonState = reading;
//}
