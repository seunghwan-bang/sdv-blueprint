//*******************************************************************************
// Project : LED Control for TIMPANI signal-based scheduling
// Board : Arduino Uno R4 WiFi
// Description : Receives signal from container (TIMPANI-N triggered) and toggles LED
//               This device receives RT-scheduled periodic signals
//*******************************************************************************
#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define N_LEDS 8

Adafruit_NeoPixel strip = Adafruit_NeoPixel(N_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

const uint32_t RED = Adafruit_NeoPixel::Color(255, 0, 0);  // TIMPANI용은 빨간색
const uint32_t OFF = 0;

bool ledOn = false;

void setup() {
    strip.setBrightness(100);
    strip.begin();
    showAll(OFF);

    Serial.begin(115200);
    while (!Serial) { }
    Serial.println("LED TIMPANI Ready - Waiting for RT signals...");
}

void showAll(uint32_t c) {
    for (uint16_t i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, c);
    }
    strip.show();
}

void loop() {
    if (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '1') {
            ledOn = !ledOn;  // 토글
            showAll(ledOn ? RED : OFF);
        } else if (c == '0') {
            ledOn = false;
            showAll(OFF);
        }
    }
    delay(1);
}
