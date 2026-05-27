//*******************************************************************************
// Project : Rotary Encoder + Button
// Board : Arduino Uno R4 WiFi
// Features: CW/CCW rotation detection + Button press detection
//*******************************************************************************
#include <Adafruit_NeoPixel.h>

#define ENCODER_A_PIN 5
#define ENCODER_B_PIN 6
#define BUTTON_PIN 7       // Button on rotary encoder
#define LED_PIN 8
#define N_LEDS 8

Adafruit_NeoPixel strip = Adafruit_NeoPixel(N_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

const uint32_t PURPLE = Adafruit_NeoPixel::Color(128, 0, 128);  // CW color
const uint32_t GREEN = Adafruit_NeoPixel::Color(0, 100, 0);     // CCW color
const uint32_t BLUE = Adafruit_NeoPixel::Color(0, 0, 255);      // Button color
const uint32_t RED = Adafruit_NeoPixel::Color(255, 0, 0);       // Ignored action color
const uint32_t OFF = 0;

// Encoder click accumulation
int cwClicks = 0;
int ccwClicks = 0;
const int CLICK_THRESHOLD = 1;  // Immediate response

// LED timing
unsigned long ledStartTime = 0;
bool ledOn = false;
const unsigned long LED_DURATION = 1000;  // 1 second

int getEncoderTurn() {
  static int oldA = 0;
  static int oldB = 0;
  int result = 0;
  int newA = digitalRead(ENCODER_A_PIN);
  int newB = digitalRead(ENCODER_B_PIN);
  if (newA != oldA || newB != oldB){
    if (!oldA && newA){
      result = -(oldB * 2 - 1);
    }
  }
  oldA = newA;
  oldB = newB;
  return result;
}

void showAll(uint32_t c) {
    for (uint16_t i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, c);
    }
    strip.show();
}

void setup() {
    strip.setBrightness(60);
    strip.begin();
    showAll(OFF);

    pinMode(ENCODER_A_PIN, INPUT);
    pinMode(ENCODER_B_PIN, INPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    Serial.begin(115200);
    delay(100);
    Serial.println("[GEAR] Ready");
    
}

void loop() {
    // Check for LED color commands from bridge.py
    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        
        if (cmd == "RED") {
            showAll(RED);
            ledOn = true;
            ledStartTime = millis();
        } else if (cmd == "PURPLE") {
            showAll(PURPLE);
            ledOn = true;
            ledStartTime = millis();
        } else if (cmd == "GREEN") {
            showAll(GREEN);
            ledOn = true;
            ledStartTime = millis();
        }
    }
    
    // Button handling
    static int prevBtn = 1;  // Button not pressed (pullup)
    int btn = digitalRead(BUTTON_PIN);
    
    if (prevBtn == 1 && btn == 0) {
        // Button pressed
        Serial.println("BTN");
        showAll(BLUE);
        ledOn = true;
        ledStartTime = millis();
    }
    prevBtn = btn;
    
    // Rotary encoder handling
    int change = getEncoderTurn();
    
    if (change != 0) {
        if (change > 0) {  // 시계방향 (CW)
            cwClicks++;
            if (cwClicks >= CLICK_THRESHOLD) {
                Serial.println("CW");
                cwClicks = 0;
            }
        } else {  // change < 0, 반시계방향 (CCW)
            ccwClicks++;
            if (ccwClicks >= CLICK_THRESHOLD) {
                Serial.println("CCW");
                ccwClicks = 0;
            }
        }
    }
    
    // Auto turn off LED after 1 second
    if (ledOn && (millis() - ledStartTime >= LED_DURATION)) {
        showAll(OFF);
        ledOn = false;
    }
    
    delay(1);
}