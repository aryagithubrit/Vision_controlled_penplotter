#define DIR_NEMA23 4
#define STEP_NEMA23 5
#define ENA_NEMA23 8  // Enable for TB6600

#define DIR_NEMA17 2
#define STEP_NEMA17 3
#define ENA_NEMA17 7  // Enable for A4988

// Configuration
int stepDelayNEMA23 = 1000;  // Microseconds (TB6600)
int stepDelayNEMA17 = 10;    // Reduced delay for A4988

// Movement boundaries (adjust per paper size)
int xMaxSteps = 400;  // X-axis (NEMA 23)
int yMaxSteps = 400;  // Y-axis (NEMA 17)

int currentX = 0, currentY = 0;  // Track motor positions

void setup() {
  // Set pins as outputs
  pinMode(DIR_NEMA23, OUTPUT);
  pinMode(STEP_NEMA23, OUTPUT);
  pinMode(ENA_NEMA23, OUTPUT);

  pinMode(DIR_NEMA17, OUTPUT);
  pinMode(STEP_NEMA17, OUTPUT);
  pinMode(ENA_NEMA17, OUTPUT);

  // Enable drivers
  digitalWrite(ENA_NEMA23, LOW);  // Enable TB6600
  digitalWrite(ENA_NEMA17, LOW);  // Enable A4988
  digitalWrite(DIR_NEMA23, LOW);
  digitalWrite(DIR_NEMA17, LOW);

  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    int commaIndex = data.indexOf(',');
    if (commaIndex != -1) {
      int x = data.substring(0, commaIndex).toInt();
      int y = data.substring(commaIndex + 1).toInt();

      // Convert to motor steps
      int targetX = map(x, 0, 100, 0, xMaxSteps);
      int targetY = map(y, 0, 100, 0, yMaxSteps);

      // Ensure target steps are within boundaries
      targetX = constrain(targetX, 0, xMaxSteps);
      targetY = constrain(targetY, 0, yMaxSteps);

      // Move motors
      moveMotors(targetX - currentX, targetY - currentY);

      // Update positions
      currentX = targetX;
      currentY = targetY;
    }
  }
}

// Function to move both motors simultaneously
void moveMotors(int deltaX, int deltaY) {
  digitalWrite(DIR_NEMA23, deltaX > 0 ? HIGH : LOW);
  digitalWrite(DIR_NEMA17, deltaY > 0 ? HIGH : LOW);

  int stepsX = abs(deltaX);
  int stepsY = abs(deltaY);
  int maxSteps = max(stepsX, stepsY);

  for (int i = 0; i < maxSteps; i++) {
    if (i < stepsX) {
      digitalWrite(STEP_NEMA23, HIGH);
      delayMicroseconds(stepDelayNEMA23);
      digitalWrite(STEP_NEMA23, LOW);
      delayMicroseconds(stepDelayNEMA23);
    }
    if (i < stepsY) {
      digitalWrite(STEP_NEMA17, HIGH);
      delayMicroseconds(stepDelayNEMA17);
      digitalWrite(STEP_NEMA17, LOW);
      delayMicroseconds(stepDelayNEMA17);
    }
  }
}
