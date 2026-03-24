/*
  The code reads values from a joystick module and prints them on the serial monitor. 
  The joystick module has two analog axes (X and Y), which are connected to Arduino 
  pins A0 and A1. The decimal form of the X and Y axis values is read and displayed 
  on the serial monitor.

  Board: Arduino Uno R4 
  Component: Joystick Module
*/

const int xPin = A0;  //the VRX attach to
const int yPin = A1;  //the VRY attach to
const int swPin = 8;  //the SW attach to

void setup() {
    Serial.begin(115200);
    while (!Serial) { }
    pinMode(swPin, INPUT_PULLUP);
    Serial.println("ts_ms, x, y, btn");
}

void loop() {
    unsigned long t = millis();
    int x = analogRead(xPin);
    int y = analogRead(yPin);
    int btn = digitalRead(swPin);

    Serial.print(t);
    Serial.print(",");
    Serial.print(x);
    Serial.print(",");
    Serial.print(y);
    Serial.print(",");
    Serial.println(btn);

    delay(50);
}

