/*
 * AGX Test Box Switching Controller
 * ==================================
 * ESP32 firmware for remote switching between FORM 3 (three-phase, 40A/phase)
 * and FORM 1 (single-phase, 125A commoned) on a Pacific Power Source AGX/AFX.
 *
 * Hardware:
 *   - ESP32 DevKit V1 (USB serial to laptop)
 *   - ULN2003A Darlington driver (low-side switch for 24V contactor coils)
 *   - 3x PC817 optocoupler feedback (24V -> 3.3V isolated sensing)
 *   - NC auxiliary contacts for hardware interlock (independent of software)
 *   - NC mushroom-head E-stop in +24V supply (hardware, independent of ESP32)
 *   - NO pushbutton E-stop to GPIO35 (software)
 *
 * Supply Rails:
 *   - +24VDC from DIN-rail PSU (contactor coils via ULN2003 COM)
 *   - 0V shared ground between 24V and ESP32 GND
 *   - 3.3V from ESP32 USB regulator (logic only)
 *
 * Serial Protocol (115200 baud):
 *   Commands (host -> ESP32):
 *     '3'  - Switch to FORM 3 (three-phase, individual loads)
 *     '1'  - Switch to FORM 1 (single-phase, commoned 125A)
 *     'S'  - Query current status
 *     '0'  - All OFF (safe state)
 *     'T'  - Run self-test (verify feedback matches drive state)
 *
 *   Responses (ESP32 -> host):
 *     OK:FORM3          - Successfully switched to FORM 3
 *     OK:FORM1          - Successfully switched to FORM 1
 *     OK:OFF            - All contactors off
 *     FAULT:<reason>    - Fault condition, all outputs disabled
 *     STATUS:<state>    - Current state report
 *     ESTOP             - E-stop pressed, all outputs disabled
 *
 * Author:  AGX Test Box Project
 * Date:    2026-03-19
 * Rev:     1.0
 */

#include <Arduino.h>

// ═══════════════════════════════════════════════════
// PIN DEFINITIONS
// ═══════════════════════════════════════════════════

// Drive outputs (ESP32 -> ULN2003A inputs)
#define PIN_DRV_FORM3   25    // ULN IN1 -> K3A/K3B/K3C coils (via interlock)
#define PIN_DRV_K1      26    // ULN IN2 -> K1A/K1B/K1C coils (via interlock)
#define PIN_DRV_KSP     27    // ULN IN3 -> KSP coil (via interlock)

// Feedback inputs (PC817 opto collectors -> ESP32)
// LOW = contactor energised (opto conducting), HIGH = contactor off
#define PIN_FB_K3       32    // K3 auxiliary NO contact -> opto -> GPIO32
#define PIN_FB_K1       33    // K1 auxiliary NO contact -> opto -> GPIO33
#define PIN_FB_KSP      34    // KSP auxiliary NO contact -> opto -> GPIO34

// E-stop input (NO pushbutton to GND, internal pull-up)
#define PIN_ESTOP       35    // LOW = E-stop pressed

// LED outputs
#define PIN_LED_GREEN   18    // FORM 3 active
#define PIN_LED_BLUE    19    // FORM 1 active
#define PIN_LED_RED     21    // Fault indicator

// ═══════════════════════════════════════════════════
// TIMING CONSTANTS
// ═══════════════════════════════════════════════════

#define CONTACTOR_OPEN_MS     150   // Time to wait for contactors to open
#define CONTACTOR_CLOSE_MS    150   // Time to wait for contactors to close
#define FEEDBACK_TIMEOUT_MS   500   // Max time to wait for feedback confirmation
#define DEBOUNCE_MS           50    // E-stop debounce time
#define LED_FAULT_BLINK_MS    300   // Fault LED blink interval
#define SERIAL_BAUD           115200

// ═══════════════════════════════════════════════════
// STATE MACHINE
// ═══════════════════════════════════════════════════

enum SystemState {
    STATE_OFF,          // All contactors off, safe state
    STATE_FORM3,        // FORM 3 active (three-phase, 40A/phase)
    STATE_FORM1,        // FORM 1 active (single-phase, 125A commoned)
    STATE_SWITCHING,    // Transition in progress
    STATE_FAULT,        // Fault detected, all outputs disabled
    STATE_ESTOP         // E-stop active, all outputs disabled
};

const char* stateNames[] = {
    "OFF", "FORM3", "FORM1", "SWITCHING", "FAULT", "ESTOP"
};

volatile SystemState currentState = STATE_OFF;
String faultReason = "";
unsigned long lastFaultBlink = 0;
bool faultLedState = false;

// ═══════════════════════════════════════════════════
// FUNCTION DECLARATIONS
// ═══════════════════════════════════════════════════

void allOutputsOff();
void setLeds(bool green, bool blue, bool red);
bool readFeedback(int pin);
bool verifyAllOpen();
bool verifyForm3Active();
bool verifyForm1Active();
bool waitForFeedback(bool (*checkFunc)(), unsigned long timeoutMs);
void switchToForm3();
void switchToForm1();
void switchToOff();
void enterFault(const char* reason);
void checkEstop();
void reportStatus();
void runSelfTest();
void processCommand(char cmd);
void updateLeds();

// ═══════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════

void setup() {
    Serial.begin(SERIAL_BAUD);

    // Configure drive outputs
    pinMode(PIN_DRV_FORM3, OUTPUT);
    pinMode(PIN_DRV_K1, OUTPUT);
    pinMode(PIN_DRV_KSP, OUTPUT);

    // Configure LED outputs
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_BLUE, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);

    // Configure feedback inputs (external pull-ups via 10k to 3.3V)
    pinMode(PIN_FB_K3, INPUT);
    pinMode(PIN_FB_K1, INPUT);
    pinMode(PIN_FB_KSP, INPUT);

    // Configure E-stop input with internal pull-up
    pinMode(PIN_ESTOP, INPUT_PULLUP);

    // Start in safe state
    allOutputsOff();
    setLeds(false, false, false);
    currentState = STATE_OFF;

    // Brief startup LED test
    setLeds(true, false, false); delay(200);
    setLeds(false, true, false); delay(200);
    setLeds(false, false, true); delay(200);
    setLeds(false, false, false); delay(200);

    Serial.println();
    Serial.println("====================================");
    Serial.println("AGX Test Box Switching Controller");
    Serial.println("Rev 1.0 | 2026-03-19");
    Serial.println("====================================");
    Serial.println("Commands: '3'=FORM3  '1'=FORM1  '0'=OFF  'S'=Status  'T'=Test");
    Serial.println("STATUS:OFF");

    // Check if E-stop is already pressed at startup
    checkEstop();
}

// ═══════════════════════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════════════════════

void loop() {
    // Always check E-stop first (highest priority)
    checkEstop();

    // Process serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        // Ignore whitespace
        if (cmd != '\n' && cmd != '\r' && cmd != ' ') {
            processCommand(cmd);
        }
    }

    // Update LED indicators
    updateLeds();
}

// ═══════════════════════════════════════════════════
// OUTPUT CONTROL
// ═══════════════════════════════════════════════════

void allOutputsOff() {
    digitalWrite(PIN_DRV_FORM3, LOW);
    digitalWrite(PIN_DRV_K1, LOW);
    digitalWrite(PIN_DRV_KSP, LOW);
}

void setLeds(bool green, bool blue, bool red) {
    digitalWrite(PIN_LED_GREEN, green ? HIGH : LOW);
    digitalWrite(PIN_LED_BLUE, blue ? HIGH : LOW);
    digitalWrite(PIN_LED_RED, red ? HIGH : LOW);
}

// ═══════════════════════════════════════════════════
// FEEDBACK READING
// ═══════════════════════════════════════════════════

// Read optocoupler feedback: LOW = contactor energised, HIGH = contactor off
bool readFeedback(int pin) {
    // Read multiple times for noise rejection
    int count = 0;
    for (int i = 0; i < 5; i++) {
        if (digitalRead(pin) == LOW) count++;
        delayMicroseconds(100);
    }
    return (count >= 3);  // Majority vote: true = energised
}

bool verifyAllOpen() {
    return !readFeedback(PIN_FB_K3) &&
           !readFeedback(PIN_FB_K1) &&
           !readFeedback(PIN_FB_KSP);
}

bool verifyForm3Active() {
    return readFeedback(PIN_FB_K3) &&
           !readFeedback(PIN_FB_K1) &&
           !readFeedback(PIN_FB_KSP);
}

bool verifyForm1Active() {
    return !readFeedback(PIN_FB_K3) &&
           readFeedback(PIN_FB_K1) &&
           readFeedback(PIN_FB_KSP);
}

bool waitForFeedback(bool (*checkFunc)(), unsigned long timeoutMs) {
    unsigned long start = millis();
    while (millis() - start < timeoutMs) {
        if (checkFunc()) return true;
        // Check E-stop during wait
        if (digitalRead(PIN_ESTOP) == LOW) return false;
        delay(10);
    }
    return false;
}

// ═══════════════════════════════════════════════════
// SWITCHING SEQUENCES
// ═══════════════════════════════════════════════════

/*
 * Mode-change sequence (break-before-make):
 * 1. De-energise current contactor group
 * 2. Wait for contactors to open
 * 3. Verify via feedback that all contacts are open
 * 4. Energise new contactor group
 * 5. Wait for contactors to close
 * 6. Verify via feedback that new group is active
 * 7. Update LEDs and report result
 *
 * If any verification fails -> FAULT state, all outputs OFF
 */

void switchToForm3() {
    if (currentState == STATE_FAULT || currentState == STATE_ESTOP) {
        Serial.println("FAULT:Cannot switch - clear fault/estop first");
        return;
    }
    if (currentState == STATE_FORM3) {
        Serial.println("OK:FORM3 (already active)");
        return;
    }

    Serial.println("SWITCHING:OFF -> FORM3...");
    currentState = STATE_SWITCHING;

    // Step 1: De-energise everything
    allOutputsOff();
    Serial.println("  Step 1: All outputs OFF");

    // Step 2: Wait for contactors to open
    delay(CONTACTOR_OPEN_MS);
    Serial.println("  Step 2: Waited for open");

    // Step 3: Verify all contacts open
    if (!waitForFeedback(verifyAllOpen, FEEDBACK_TIMEOUT_MS)) {
        enterFault("Contacts did not open (feedback mismatch after de-energise)");
        return;
    }
    Serial.println("  Step 3: Verified all OPEN");

    // Step 4: Energise FORM 3 group (K3A/K3B/K3C via ULN OUT1)
    digitalWrite(PIN_DRV_FORM3, HIGH);
    Serial.println("  Step 4: K3 drive HIGH");

    // Step 5: Wait for contactors to close
    delay(CONTACTOR_CLOSE_MS);
    Serial.println("  Step 5: Waited for close");

    // Step 6: Verify FORM 3 is active
    if (!waitForFeedback(verifyForm3Active, FEEDBACK_TIMEOUT_MS)) {
        enterFault("FORM3 feedback mismatch (K3 did not confirm closed)");
        return;
    }
    Serial.println("  Step 6: Verified FORM3 active");

    // Success
    currentState = STATE_FORM3;
    Serial.println("OK:FORM3");
}

void switchToForm1() {
    if (currentState == STATE_FAULT || currentState == STATE_ESTOP) {
        Serial.println("FAULT:Cannot switch - clear fault/estop first");
        return;
    }
    if (currentState == STATE_FORM1) {
        Serial.println("OK:FORM1 (already active)");
        return;
    }

    Serial.println("SWITCHING:OFF -> FORM1...");
    currentState = STATE_SWITCHING;

    // Step 1: De-energise everything
    allOutputsOff();
    Serial.println("  Step 1: All outputs OFF");

    // Step 2: Wait for contactors to open
    delay(CONTACTOR_OPEN_MS);
    Serial.println("  Step 2: Waited for open");

    // Step 3: Verify all contacts open
    if (!waitForFeedback(verifyAllOpen, FEEDBACK_TIMEOUT_MS)) {
        enterFault("Contacts did not open (feedback mismatch after de-energise)");
        return;
    }
    Serial.println("  Step 3: Verified all OPEN");

    // Step 4: Energise FORM 1 group (K1 combine + KSP output)
    digitalWrite(PIN_DRV_K1, HIGH);
    digitalWrite(PIN_DRV_KSP, HIGH);
    Serial.println("  Step 4: K1+KSP drive HIGH");

    // Step 5: Wait for contactors to close
    delay(CONTACTOR_CLOSE_MS);
    Serial.println("  Step 5: Waited for close");

    // Step 6: Verify FORM 1 is active
    if (!waitForFeedback(verifyForm1Active, FEEDBACK_TIMEOUT_MS)) {
        enterFault("FORM1 feedback mismatch (K1+KSP did not confirm closed)");
        return;
    }
    Serial.println("  Step 6: Verified FORM1 active");

    // Success
    currentState = STATE_FORM1;
    Serial.println("OK:FORM1");
}

void switchToOff() {
    allOutputsOff();
    delay(CONTACTOR_OPEN_MS);

    if (currentState != STATE_ESTOP) {
        // Verify contacts opened (skip during E-stop to avoid masking)
        if (!waitForFeedback(verifyAllOpen, FEEDBACK_TIMEOUT_MS)) {
            enterFault("Contacts did not open after OFF command");
            return;
        }
    }

    currentState = STATE_OFF;
    faultReason = "";
    Serial.println("OK:OFF");
}

// ═══════════════════════════════════════════════════
// FAULT HANDLING
// ═══════════════════════════════════════════════════

void enterFault(const char* reason) {
    allOutputsOff();
    currentState = STATE_FAULT;
    faultReason = reason;
    Serial.print("FAULT:");
    Serial.println(reason);
}

void checkEstop() {
    static unsigned long lastEstopCheck = 0;
    static bool lastEstopState = false;

    // Debounce
    if (millis() - lastEstopCheck < DEBOUNCE_MS) return;
    lastEstopCheck = millis();

    bool estopPressed = (digitalRead(PIN_ESTOP) == LOW);

    if (estopPressed && !lastEstopState) {
        // E-stop just pressed
        allOutputsOff();
        currentState = STATE_ESTOP;
        Serial.println("ESTOP");
        Serial.println("  All outputs disabled. Press '0' to reset after releasing E-stop.");
    }

    lastEstopState = estopPressed;
}

// ═══════════════════════════════════════════════════
// STATUS AND SELF-TEST
// ═══════════════════════════════════════════════════

void reportStatus() {
    Serial.println("────────────────────────────────");
    Serial.print("STATUS:");
    Serial.println(stateNames[currentState]);

    Serial.print("  Drive: FORM3=");
    Serial.print(digitalRead(PIN_DRV_FORM3) ? "ON" : "off");
    Serial.print(" K1=");
    Serial.print(digitalRead(PIN_DRV_K1) ? "ON" : "off");
    Serial.print(" KSP=");
    Serial.println(digitalRead(PIN_DRV_KSP) ? "ON" : "off");

    Serial.print("  Feedback: K3=");
    Serial.print(readFeedback(PIN_FB_K3) ? "CLOSED" : "open");
    Serial.print(" K1=");
    Serial.print(readFeedback(PIN_FB_K1) ? "CLOSED" : "open");
    Serial.print(" KSP=");
    Serial.println(readFeedback(PIN_FB_KSP) ? "CLOSED" : "open");

    Serial.print("  E-stop: ");
    Serial.println(digitalRead(PIN_ESTOP) == LOW ? "PRESSED" : "released");

    if (currentState == STATE_FAULT) {
        Serial.print("  Fault reason: ");
        Serial.println(faultReason);
    }
    Serial.println("────────────────────────────────");
}

void runSelfTest() {
    Serial.println("SELFTEST:Starting...");

    // Must be in OFF state
    if (currentState != STATE_OFF) {
        Serial.println("SELFTEST:FAIL - must be in OFF state first ('0')");
        return;
    }

    // Check all feedback shows open
    Serial.print("  All contacts open: ");
    if (verifyAllOpen()) {
        Serial.println("PASS");
    } else {
        Serial.println("FAIL - feedback shows contact(s) closed while drives off");
        enterFault("Self-test: contacts closed with drives off");
        return;
    }

    // Check E-stop is released
    Serial.print("  E-stop released: ");
    if (digitalRead(PIN_ESTOP) == HIGH) {
        Serial.println("PASS");
    } else {
        Serial.println("FAIL - E-stop is pressed");
        return;
    }

    // Test FORM 3
    Serial.println("  Testing FORM 3 switch...");
    switchToForm3();
    if (currentState != STATE_FORM3) {
        Serial.println("SELFTEST:FAIL - FORM 3 switch failed");
        return;
    }
    delay(500);

    // Test OFF from FORM 3
    switchToOff();
    if (currentState != STATE_OFF) {
        Serial.println("SELFTEST:FAIL - OFF from FORM 3 failed");
        return;
    }
    delay(500);

    // Test FORM 1
    Serial.println("  Testing FORM 1 switch...");
    switchToForm1();
    if (currentState != STATE_FORM1) {
        Serial.println("SELFTEST:FAIL - FORM 1 switch failed");
        return;
    }
    delay(500);

    // Test OFF from FORM 1
    switchToOff();
    if (currentState != STATE_OFF) {
        Serial.println("SELFTEST:FAIL - OFF from FORM 1 failed");
        return;
    }

    Serial.println("SELFTEST:PASS - All tests passed");
}

// ═══════════════════════════════════════════════════
// COMMAND PROCESSING
// ═══════════════════════════════════════════════════

void processCommand(char cmd) {
    switch (cmd) {
        case '3':
            switchToForm3();
            break;
        case '1':
            switchToForm1();
            break;
        case '0':
            switchToOff();
            break;
        case 'S':
        case 's':
            reportStatus();
            break;
        case 'T':
        case 't':
            runSelfTest();
            break;
        default:
            Serial.print("UNKNOWN:");
            Serial.println(cmd);
            Serial.println("Commands: '3'=FORM3  '1'=FORM1  '0'=OFF  'S'=Status  'T'=Test");
            break;
    }
}

// ═══════════════════════════════════════════════════
// LED MANAGEMENT
// ═══════════════════════════════════════════════════

void updateLeds() {
    switch (currentState) {
        case STATE_OFF:
            setLeds(false, false, false);
            break;
        case STATE_FORM3:
            setLeds(true, false, false);   // Green = FORM 3
            break;
        case STATE_FORM1:
            setLeds(false, true, false);   // Blue = FORM 1
            break;
        case STATE_SWITCHING:
            // Both green and blue during transition
            setLeds(true, true, false);
            break;
        case STATE_FAULT:
            // Blink red LED
            if (millis() - lastFaultBlink > LED_FAULT_BLINK_MS) {
                faultLedState = !faultLedState;
                lastFaultBlink = millis();
            }
            setLeds(false, false, faultLedState);
            break;
        case STATE_ESTOP:
            // Solid red
            setLeds(false, false, true);
            break;
    }
}
