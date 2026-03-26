//*******************************************************************************
// Project : 12 Passive Buzzer in Sensor Kit
// Board : Arduino Uno 
// By : Kit Plus
//*******************************************************************************

int DigitalPin = 7;  // Digital input

void setup()
{
    pinMode(DigitalPin, OUTPUT);
    Serial.begin(115200);
    while (!Serial) { }
}

void loop()
{
    // Play a tone with a frequency of 1000 Hz for 1 second
    tone(DigitalPin, 1000, 100); 
    delay(100); // Wait for the tone duration

    // Stop the tone for 1 second (noTone() stops the current tone)
    noTone(DigitalPin);
    delay(10000);
}
