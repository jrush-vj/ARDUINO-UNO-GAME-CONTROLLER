const int joyLX = A0;
const int joyLY = A1;
const int joyRX = A2;
const int joyRY = A3;
const int triggerL = A4;
const int triggerR = A5;

const int buttonY = 2;
const int buttonX = 3;
const int buttonA = 4;
const int buttonB = 5;
const int buttonLSW = 6;
const int buttonRSW = 7;

const unsigned long SERIAL_BAUD = 9600;
const unsigned long REPORT_INTERVAL = 10;
const int JOYSTICK_SAMPLES = 3;
const int DEADZONE = 20;

int xLeftFiltered, yLeftFiltered, xRightFiltered, yRightFiltered;
int ltFiltered = 0, rtFiltered = 0;

int xLeftOffset = 0, yLeftOffset = 0, xRightOffset = 0, yRightOffset = 0;
unsigned long lastReportTime = 0;

void setup() {
  Serial.begin(SERIAL_BAUD);

  pinMode(buttonY, INPUT_PULLUP);
  pinMode(buttonA, INPUT_PULLUP);
  pinMode(buttonX, INPUT_PULLUP);
  pinMode(buttonB, INPUT_PULLUP);
  pinMode(buttonLSW, INPUT_PULLUP);
  pinMode(buttonRSW, INPUT_PULLUP);

  delay(500);
  calibrateJoysticks();
}

void calibrateJoysticks() {
  int samplesX[2] = {0}, samplesY[2] = {0};

  for (int i = 0; i < 10; i++) {
    samplesX[0] += analogRead(joyLX);
    samplesY[0] += analogRead(joyLY);
    samplesX[1] += analogRead(joyRX);
    samplesY[1] += analogRead(joyRY);
    delay(5);
  }

  xLeftOffset = (samplesX[0] / 10) - 512;
  yLeftOffset = (samplesY[0] / 10) - 512;
  xRightOffset = (samplesX[1] / 10) - 512;
  yRightOffset = (samplesY[1] / 10) - 512;

  xLeftFiltered = analogRead(joyLX);
  yLeftFiltered = analogRead(joyLY);
  xRightFiltered = analogRead(joyRX);
  yRightFiltered = analogRead(joyRY);
  ltFiltered = 0;
  rtFiltered = 0;
}

int readJoystick(int pin, int &filteredValue, int offset) {
  int current = analogRead(pin);
  filteredValue = (filteredValue * (JOYSTICK_SAMPLES - 1) + current) / JOYSTICK_SAMPLES;
  int centered = filteredValue - 512 - offset;
  
  // Ensure the centered value stays within the range 0 to 1024
  if (abs(centered) < DEADZONE) return 512;
  
  int result = centered + 512;
  
  // Constrain the result between 0 and 1024
  if (result < 0) return 0;
  if (result > 1024) return 1024;
  
  return result;
}


// Modified: pull up = increase value, default at 0
int readTriggerJoystick(int pin, int &filteredValue) {
  int current = analogRead(pin);
  filteredValue = (filteredValue * (JOYSTICK_SAMPLES - 1) + current) / JOYSTICK_SAMPLES;
  int pull = 512 - filteredValue;
  if (pull < DEADZONE) return 0;
  int range = pull;
  if (range > 512) range = 512;
  return range;
}

void loop() {
  if (millis() - lastReportTime < REPORT_INTERVAL) return;
  lastReportTime = millis();

  int xL = readJoystick(joyLX, xLeftFiltered, xLeftOffset);
  int yL = readJoystick(joyLY, yLeftFiltered, yLeftOffset);
  int xR = readJoystick(joyRX, xRightFiltered, xRightOffset);
  int yR = readJoystick(joyRY, yRightFiltered, yRightOffset);
  int lt = readTriggerJoystick(triggerL, ltFiltered);
  int rt = readTriggerJoystick(triggerR, rtFiltered);

  int yBtn = !digitalRead(buttonY);
  int aBtn = !digitalRead(buttonA);
  int xBtn = !digitalRead(buttonX);
  int bBtn = !digitalRead(buttonB);
  int lsw  = !digitalRead(buttonLSW);
  int rsw  = !digitalRead(buttonRSW);

  Serial.print(xL); Serial.print(",");
  Serial.print(yL); Serial.print(",");
  Serial.print(xR); Serial.print(",");
  Serial.print(yR); Serial.print(",");
  Serial.print(lt); Serial.print(",");
  Serial.print(rt); Serial.print(",");
  Serial.print(yBtn); Serial.print(",");
  Serial.print(aBtn); Serial.print(",");
  Serial.print(xBtn); Serial.print(",");
  Serial.print(bBtn); Serial.print(",");
  Serial.print(lsw); Serial.print(",");
  Serial.println(rsw);
}
