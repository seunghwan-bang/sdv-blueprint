#include <Adafruit_NeoPixel.h>
#define PIN 6
#define N_LEDS 8

Adafruit_NeoPixel strip = Adafruit_NeoPixel(N_LEDS, PIN, NEO_GRB + NEO_KHZ800);   

const uint32_t RED = Adafruit_NeoPixel::Color(255, 0, 0);
const uint32_t YELLOW = Adafruit_NeoPixel::Color(255, 180, 0);
const uint32_t OFF = 0;

const int LEFT_ON = 200;
const int LEFT_OFF = 260;
const int RIGHT_ON = 823;
const int RIGHT_OFF = 763;

char lineBuf[64];
size_t lineLen = 0;
unsigned long lastRxMs = 0;
const unsigned long RX_TIMEOUT_MS = 3000;

int lastBtn = -1;
int lastMode = -1;
unsigned long lastBtnChangeMs = 0;
const unsigned long DEBOUNCE_MS = 30;

enum Mode {
  MODE_OFF = 0,
  MODE_LEFT_Y = 1,
  MODE_RIGHT_Y = 2,
  MODE_CENTER_R = 3
};

void showAll(uint32_t c) {
  for (uint16_t i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, c);
  }
  strip.show();
}

void showIndices(uint16_t i0, uint16_t i1, uint32_t c) {
  for (uint16_t i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, OFF);
  }
  if (i0 < strip.numPixels()) strip.setPixelColor(i0, c);
  if (i1 < strip.numPixels()) strip.setPixelColor(i1, c);
  strip.show();
}

void showCenterRed() {
  for (uint16_t i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, OFF);
  }

  uint16_t n = strip.numPixels();
  if (n == 0) {
    strip.show();
    return;
  }
  if ((n % 2) == 0) {
    uint16_t right = n / 2;
    uint16_t left = right - 1;
    showIndices(left, right, RED);
  } else {
    uint16_t mid = n / 2;
    strip.setPixelColor(mid, RED);
  }
  strip.show();
}

void applyMode(int mode) {
  if (mode == lastMode) return;
  switch (mode) {
    case MODE_OFF:
      showAll(OFF);
      break;
    case MODE_LEFT_Y:
      showIndices(0,1, YELLOW);
      break;
    case MODE_RIGHT_Y:
      showIndices(strip.numPixels()-2, strip.numPixels()-1, YELLOW);
      break;
    case MODE_CENTER_R:
      showCenterRed();
      break;
  }
  lastMode = mode;
}

//void applyBtn(int btn) {
//  if (btn == lastBtn) return;
//  if (btn == 0) {
//    showOnlyCenters(RED);
//  } else if (btn == 1) {
//    showAll(OFF);
//  } else {
//    return;
//  }
//
//  lastBtn = btn;
//  lastBtnChangeMs = millis();
//}

void setup() {
  strip.setBrightness(100);
  strip.begin();
  showAll(OFF);

  Serial.begin(115200);
  // while (!Serial) { }
  lastRxMs = millis();
}

bool parse_x_btn(const char* s, int& x_out, int& btn_out) {
  int ccount = 0;
  for (const char* p=s; *p; ++p) if (*p==',') ccount++;

  if (ccount == 1) {
    int x = -1, btn = -1;
    long a,b;
    if (sscanf(s, "%ld,%ld", &a, &b) == 2) {
      x = (int)a; btn = (int)b;
      if (0 <= x && x <= 1023 && (btn==0 || btn==1)) {
        x_out = x; btn_out = btn;
        return true;
      }
    }
  }

  return false;
}

int parseButtonFromLine(const char* s) {
  int lastDigit = -1;
  for (size_t i = 0; s[i]; ++i) {
    if (s[i] == '0' || s[i] =='1') {
      lastDigit = s[i] - '0';
    }
  }
  return lastDigit;
}

void handleButton(int btn) {
  if (btn == 0) {
    showAll(RED);
  } else if (btn == 1) {
    showAll(OFF);
  }
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      lineBuf[lineLen] = '\0';
      int x=-1, btn=-1;

      if (parse_x_btn(lineBuf, x, btn)) {
        lastRxMs = millis();

        if (btn == 0) {
          applyMode(MODE_CENTER_R);
          lastBtn = 0;
        } else if (btn == 1) {
          static bool leftOn = false;
          static bool rightOn = false;
          
          if (!leftOn) {
            if (x <= LEFT_ON) {leftOn = true; rightOn= false;}
          } else {
            if (x >= LEFT_OFF) { leftOn = false;}
          }

          if (!rightOn) {
            if (x >= RIGHT_ON) {rightOn = true; leftOn = false;}
          } else {
            if (x <= RIGHT_OFF) {rightOn = false;}
          }

          if (leftOn) applyMode(MODE_LEFT_Y);
          else if (rightOn) applyMode(MODE_RIGHT_Y);
          else applyMode(MODE_OFF);

          lastBtn = 1;
        }
      }
      lineLen = 0;
    } else {
      if (lineLen < sizeof(lineBuf)-1) {
        lineBuf[lineLen++] = c;
      } else {
        lineLen = 0;
      }
    }
  }

  if (millis() - lastRxMs > RX_TIMEOUT_MS) {
    applyMode(MODE_OFF);
    lastBtn = 1;
    lastRxMs = millis();
  }
}

//static void chase(uint32_t c) {
//  for(uint16_t i=0; i<strip.numPixels()+4; i++) {
//      strip.setPixelColor(i  , c); // i 번째 픽셀에 LED 색상 지정
//      strip.setPixelColor(i-3, 0); // i-3 픽셀에 색상 0을 지정하여 지움
//      strip.show(); // 
//      delay(10);
//  }
//} 
