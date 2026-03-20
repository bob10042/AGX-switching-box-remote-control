/*
 * AGX Test Box Switching Controller - Rev 2.0
 * ============================================
 * ESP32 firmware for remote switching of individual phases and combined
 * modes on a Pacific Power Source AGX/AFX programmable AC source.
 *
 * Modes:
 *   PHASE A - Phase A only via K3A (40A)
 *   PHASE B - Phase B only via K3B (40A)
 *   PHASE C - Phase C only via K3C (40A)
 *   FORM 3  - All three phases via K3A+K3B+K3C (40A/phase)
 *   FORM 1  - Single-phase commoned via K1+KSP (125A)
 *
 * Hardware:
 *   - ESP32 DevKit V1 (USB serial to laptop)
 *   - ULN2003A Darlington driver (5 channels: K3A, K3B, K3C, K1, KSP)
 *   - 5x PC817 optocoupler feedback (24V -> 3.3V isolated sensing)
 *   - NC auxiliary contacts for hardware interlock (independent of software)
 *   - NC mushroom-head E-stop in +24V supply (hardware, independent of ESP32)
 *   - NO pushbutton E-stop to GPIO35 (software)
 *
 * Drive Outputs (ESP32 -> ULN2003A):
 *   GPIO25 -> ULN IN1 -> OUT1 -> K3A coil (Phase A, 40A)
 *   GPIO26 -> ULN IN2 -> OUT2 -> K3B coil (Phase B, 40A)
 *   GPIO27 -> ULN IN3 -> OUT3 -> K3C coil (Phase C, 40A)
 *   GPIO16 -> ULN IN4 -> OUT4 -> K1  coil (FORM1 combine, 3x40A)
 *   GPIO17 -> ULN IN5 -> OUT5 -> KSP coil (FORM1 output, 125A)
 *
 * Feedback Inputs (PC817 opto collectors -> ESP32):
 *   GPIO32 <- K3A auxiliary NO contact (LOW = closed)
 *   GPIO33 <- K3B auxiliary NO contact (LOW = closed)
 *   GPIO34 <- K3C auxiliary NO contact (LOW = closed)
 *   GPIO36 <- K1  auxiliary NO contact (LOW = closed)
 *   GPIO39 <- KSP auxiliary NO contact (LOW = closed)
 *
 * Hardware Interlock (NC auxiliary contacts in coil supply paths):
 *   K3 bus: +24V -> K1_NC -> KSP_NC -> K3A/K3B/K3C coils
 *   K1 bus: +24V -> K3A_NC -> K3B_NC -> K3C_NC -> K1/KSP coils
 *
 * Serial Protocol (115200 baud):
 *   Commands:
 *     'A'  - Phase A only (K3A)
 *     'B'  - Phase B only (K3B)
 *     'C'  - Phase C only (K3C)
 *     '3'  - FORM 3 (all three phases, K3A+K3B+K3C)
 *     '1'  - FORM 1 (single-phase commoned, K1+KSP, 125A)
 *     '0'  - All OFF (safe state)
 *     'S'  - Query current status
 *     'T'  - Run self-test
 *
 *   Responses:
 *     OK:PHASE_A        - Phase A active
 *     OK:PHASE_B        - Phase B active
 *     OK:PHASE_C        - Phase C active
 *     OK:FORM3          - All three phases active
 *     OK:FORM1          - Single-phase commoned active
 *     OK:OFF            - All contactors off
 *     FAULT:<reason>    - Fault condition, all outputs disabled
 *     STATUS:<state>    - Current state report
 *     ESTOP             - E-stop pressed, all outputs disabled
 *
 * Author:  AGX Test Box Project
 * Date:    2026-03-20
 * Rev:     2.0
 */

#include <Arduino.h>

// =======================================================
// PIN DEFINITIONS
// =======================================================

// Drive outputs (ESP32 -> ULN2003A inputs, 5 channels)
#define PIN_DRV_K3A     25    // ULN IN1 -> K3A coil (Phase A)
#define PIN_DRV_K3B     26    // ULN IN2 -> K3B coil (Phase B)
#define PIN_DRV_K3C     27    // ULN IN3 -> K3C coil (Phase C)
#define PIN_DRV_K1      16    // ULN IN4 -> K1 coil  (FORM1 combine)
#define PIN_DRV_KSP     17    // ULN IN5 -> KSP coil (FORM1 output)

// Feedback inputs (PC817 opto collectors -> ESP32)
// LOW = contactor energised (opto conducting), HIGH = contactor off
#define PIN_FB_K3A      32    // K3A auxiliary NO -> opto -> GPIO32
#define PIN_FB_K3B      33    // K3B auxiliary NO -> opto -> GPIO33
#define PIN_FB_K3C      34    // K3C auxiliary NO -> opto -> GPIO34 (input-only)
#define PIN_FB_K1       36    // K1  auxiliary NO -> opto -> GPIO36 (input-only, VP)
#define PIN_FB_KSP      39    // KSP auxiliary NO -> opto -> GPIO39 (input-only, VN)

// E-stop input (NO pushbutton to GND)
#define PIN_ESTOP       35    // LOW = E-stop pressed (input-only)

// LED outputs
#define PIN_LED_GREEN   18    // Any FORM 3 phase active (A, B, C, or all)
#define PIN_LED_BLUE    19    // FORM 1 active
#define PIN_LED_RED     21    // Fault / E-stop indicator

// =======================================================
// TIMING CONSTANTS
// =======================================================

#define CONTACTOR_OPEN_MS     150   // Time for contactors to open
#define CONTACTOR_CLOSE_MS    150   // Time for contactors to close
#define FEEDBACK_TIMEOUT_MS   500   // Max wait for feedback confirmation
#define DEBOUNCE_MS           50    // E-stop debounce time
#define LED_FAULT_BLINK_MS    300   // Fault LED blink interval
#define SERIAL_BAUD           115200

// =======================================================
// STATE MACHINE
// =======================================================

enum SystemState {
    STATE_OFF,          // All contactors off, safe state
    STATE_PHASE_A,      // Phase A only (K3A)
    STATE_PHASE_B,      // Phase B only (K3B)
    STATE_PHASE_C,      // Phase C only (K3C)
    STATE_FORM3,        // All three phases (K3A+K3B+K3C)
    STATE_FORM1,        // Single-phase commoned (K1+KSP, 125A)
    STATE_SWITCHING,    // Transition in progress
    STATE_FAULT,        // Fault detected, all outputs disabled
    STATE_ESTOP         // E-stop active, all outputs disabled
};

const char* stateNames[] = {
    "OFF", "PHASE_A", "PHASE_B", "PHASE_C", "FORM3", "FORM1",
    "SWITCHING", "FAULT", "ESTOP"
};

volatile SystemState currentState = STATE_OFF;
String faultReason = "";
unsigned long lastFaultBlink = 0;
bool faultLedState = false;

// =======================================================
// FUNCTION DECLARATIONS
// =======================================================

void allOutputsOff();
void setLeds(bool green, bool blue, bool red);
bool readFeedback(int pin);
bool verifyAllOpen();
bool verifyPhaseA();
bool verifyPhaseB();
bool verifyPhaseC();
bool verifyForm3Active();
bool verifyForm1Active();
bool waitForFeedback(bool (*checkFunc)(), unsigned long timeoutMs);
void doBreakBeforeMake(const char* targetName,
                       void (*energiseFunc)(),
                       bool (*verifyFunc)(),
                       SystemState targetState);
void switchToPhaseA();
void switchToPhaseB();
void switchToPhaseC();
void switchToForm3();
void switchToForm1();
void switchToOff();
void enterFault(const char* reason);
void checkEstop();
void reportStatus();
void runSelfTest();
void processCommand(char cmd);
void updateLeds();

// =======================================================
// SETUP
// =======================================================

void setup() {
    Serial.begin(SERIAL_BAUD);

    // Configure drive outputs (5 channels)
    pinMode(PIN_DRV_K3A, OUTPUT);
    pinMode(PIN_DRV_K3B, OUTPUT);
    pinMode(PIN_DRV_K3C, OUTPUT);
    pinMode(PIN_DRV_K1,  OUTPUT);
    pinMode(PIN_DRV_KSP, OUTPUT);

    // Configure LED outputs
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_BLUE,  OUTPUT);
    pinMode(PIN_LED_RED,   OUTPUT);

    // Configure feedback inputs (all use external 10k pull-ups to 3.3V)
    // GPIO34, 36, 39 are input-only pins with no internal pull-up
    pinMode(PIN_FB_K3A, INPUT);
    pinMode(PIN_FB_K3B, INPUT);
    pinMode(PIN_FB_K3C, INPUT);
    pinMode(PIN_FB_K1,  INPUT);
    pinMode(PIN_FB_KSP, INPUT);

    // Configure E-stop input (external pull-up recommended on GPIO35)
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
    Serial.println("Rev 2.0 | 2026-03-20");
    Serial.println("Individual Phase Selection");
    Serial.println("====================================");
    Serial.println("Commands:");
    Serial.println("  'A'=PhaseA  'B'=PhaseB  'C'=PhaseC");
    Serial.println("  '3'=FORM3   '1'=FORM1   '0'=OFF");
    Serial.println("  'S'=Status  'T'=SelfTest");
    Serial.println("STATUS:OFF");

    // Check if E-stop is already pressed at startup
    checkEstop();
}

// =======================================================
// MAIN LOOP
// =======================================================

void loop() {
    // Always check E-stop first (highest priority)
    checkEstop();

    // Process serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        if (cmd != '\n' && cmd != '\r' && cmd != ' ') {
            processCommand(cmd);
        }
    }

    // Update LED indicators
    updateLeds();
}

// =======================================================
// OUTPUT CONTROL
// =======================================================

void allOutputsOff() {
    digitalWrite(PIN_DRV_K3A, LOW);
    digitalWrite(PIN_DRV_K3B, LOW);
    digitalWrite(PIN_DRV_K3C, LOW);
    digitalWrite(PIN_DRV_K1,  LOW);
    digitalWrite(PIN_DRV_KSP, LOW);
}

void setLeds(bool green, bool blue, bool red) {
    digitalWrite(PIN_LED_GREEN, green ? HIGH : LOW);
    digitalWrite(PIN_LED_BLUE,  blue  ? HIGH : LOW);
    digitalWrite(PIN_LED_RED,   red   ? HIGH : LOW);
}

// =======================================================
// FEEDBACK READING
// =======================================================

// Read optocoupler feedback: LOW = contactor energised, HIGH = contactor off
bool readFeedback(int pin) {
    int count = 0;
    for (int i = 0; i < 5; i++) {
        if (digitalRead(pin) == LOW) count++;
        delayMicroseconds(100);
    }
    return (count >= 3);  // Majority vote: true = energised
}

bool verifyAllOpen() {
    return !readFeedback(PIN_FB_K3A) &&
           !readFeedback(PIN_FB_K3B) &&
           !readFeedback(PIN_FB_K3C) &&
           !readFeedback(PIN_FB_K1)  &&
           !readFeedback(PIN_FB_KSP);
}

bool verifyPhaseA() {
    return  readFeedback(PIN_FB_K3A) &&
           !readFeedback(PIN_FB_K3B) &&
           !readFeedback(PIN_FB_K3C) &&
           !readFeedback(PIN_FB_K1)  &&
           !readFeedback(PIN_FB_KSP);
}

bool verifyPhaseB() {
    return !readFeedback(PIN_FB_K3A) &&
            readFeedback(PIN_FB_K3B) &&
           !readFeedback(PIN_FB_K3C) &&
           !readFeedback(PIN_FB_K1)  &&
           !readFeedback(PIN_FB_KSP);
}

bool verifyPhaseC() {
    return !readFeedback(PIN_FB_K3A) &&
           !readFeedback(PIN_FB_K3B) &&
            readFeedback(PIN_FB_K3C) &&
           !readFeedback(PIN_FB_K1)  &&
           !readFeedback(PIN_FB_KSP);
}

bool verifyForm3Active() {
    return  readFeedback(PIN_FB_K3A) &&
            readFeedback(PIN_FB_K3B) &&
            readFeedback(PIN_FB_K3C) &&
           !readFeedback(PIN_FB_K1)  &&
           !readFeedback(PIN_FB_KSP);
}

bool verifyForm1Active() {
    return !readFeedback(PIN_FB_K3A) &&
           !readFeedback(PIN_FB_K3B) &&
           !readFeedback(PIN_FB_K3C) &&
            readFeedback(PIN_FB_K1)  &&
            readFeedback(PIN_FB_KSP);
}

bool waitForFeedback(bool (*checkFunc)(), unsigned long timeoutMs) {
    unsigned long start = millis();
    while (millis() - start < timeoutMs) {
        if (checkFunc()) return true;
        if (digitalRead(PIN_ESTOP) == LOW) return false;
        delay(10);
    }
    return false;
}

// =======================================================
// COMMON BREAK-BEFORE-MAKE SEQUENCE
// =======================================================

/*
 * All mode changes follow this sequence:
 * 1. De-energise all contactors
 * 2. Wait for contacts to open
 * 3. Verify all contacts open via feedback
 * 4. Energise target contactor(s)
 * 5. Wait for contacts to close
 * 6. Verify target contacts closed via feedback
 * 7. Update state and report result
 */

void doBreakBeforeMake(const char* targetName,
                       void (*energiseFunc)(),
                       bool (*verifyFunc)(),
                       SystemState targetState)
{
    if (currentState == STATE_FAULT || currentState == STATE_ESTOP) {
        Serial.println("FAULT:Cannot switch - clear fault/estop first ('0')");
        return;
    }
    if (currentState == targetState) {
        Serial.print("OK:");
        Serial.print(stateNames[targetState]);
        Serial.println(" (already active)");
        return;
    }

    Serial.print("SWITCHING:");
    Serial.print(stateNames[currentState]);
    Serial.print(" -> ");
    Serial.print(targetName);
    Serial.println("...");
    currentState = STATE_SWITCHING;

    // Step 1: De-energise everything
    allOutputsOff();
    Serial.println("  Step 1: All outputs OFF");

    // Step 2: Wait for contacts to open
    delay(CONTACTOR_OPEN_MS);
    Serial.println("  Step 2: Waited for open");

    // Step 3: Verify all contacts open
    if (!waitForFeedback(verifyAllOpen, FEEDBACK_TIMEOUT_MS)) {
        enterFault("Contacts did not open (feedback mismatch after de-energise)");
        return;
    }
    Serial.println("  Step 3: Verified all OPEN");

    // Step 4: Energise target contactors
    energiseFunc();
    Serial.println("  Step 4: Target drive(s) HIGH");

    // Step 5: Wait for contacts to close
    delay(CONTACTOR_CLOSE_MS);
    Serial.println("  Step 5: Waited for close");

    // Step 6: Verify correct contacts closed
    if (!waitForFeedback(verifyFunc, FEEDBACK_TIMEOUT_MS)) {
        allOutputsOff();
        String reason = String(targetName) + " feedback mismatch (contacts did not confirm)";
        enterFault(reason.c_str());
        return;
    }
    Serial.print("  Step 6: Verified ");
    Serial.print(targetName);
    Serial.println(" active");

    // Success
    currentState = targetState;
    Serial.print("OK:");
    Serial.println(stateNames[targetState]);
}

// =======================================================
// ENERGISE FUNCTIONS (called by doBreakBeforeMake)
// =======================================================

void energisePhaseA() { digitalWrite(PIN_DRV_K3A, HIGH); }
void energisePhaseB() { digitalWrite(PIN_DRV_K3B, HIGH); }
void energisePhaseC() { digitalWrite(PIN_DRV_K3C, HIGH); }

void energiseForm3() {
    digitalWrite(PIN_DRV_K3A, HIGH);
    digitalWrite(PIN_DRV_K3B, HIGH);
    digitalWrite(PIN_DRV_K3C, HIGH);
}

void energiseForm1() {
    digitalWrite(PIN_DRV_K1,  HIGH);
    digitalWrite(PIN_DRV_KSP, HIGH);
}

// =======================================================
// SWITCHING COMMANDS
// =======================================================

void switchToPhaseA() {
    doBreakBeforeMake("PHASE_A", energisePhaseA, verifyPhaseA, STATE_PHASE_A);
}

void switchToPhaseB() {
    doBreakBeforeMake("PHASE_B", energisePhaseB, verifyPhaseB, STATE_PHASE_B);
}

void switchToPhaseC() {
    doBreakBeforeMake("PHASE_C", energisePhaseC, verifyPhaseC, STATE_PHASE_C);
}

void switchToForm3() {
    doBreakBeforeMake("FORM3", energiseForm3, verifyForm3Active, STATE_FORM3);
}

void switchToForm1() {
    doBreakBeforeMake("FORM1", energiseForm1, verifyForm1Active, STATE_FORM1);
}

void switchToOff() {
    allOutputsOff();
    delay(CONTACTOR_OPEN_MS);

    if (currentState != STATE_ESTOP) {
        if (!waitForFeedback(verifyAllOpen, FEEDBACK_TIMEOUT_MS)) {
            enterFault("Contacts did not open after OFF command");
            return;
        }
    }

    currentState = STATE_OFF;
    faultReason = "";
    Serial.println("OK:OFF");
}

// =======================================================
// FAULT HANDLING
// =======================================================

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

    if (millis() - lastEstopCheck < DEBOUNCE_MS) return;
    lastEstopCheck = millis();

    bool estopPressed = (digitalRead(PIN_ESTOP) == LOW);

    if (estopPressed && !lastEstopState) {
        allOutputsOff();
        currentState = STATE_ESTOP;
        Serial.println("ESTOP");
        Serial.println("  All outputs disabled. Press '0' to reset after releasing E-stop.");
    }

    lastEstopState = estopPressed;
}

// =======================================================
// STATUS AND SELF-TEST
// =======================================================

void reportStatus() {
    Serial.println("------------------------------------");
    Serial.print("STATUS:");
    Serial.println(stateNames[currentState]);

    Serial.print("  Drive:  K3A=");
    Serial.print(digitalRead(PIN_DRV_K3A) ? "ON" : "off");
    Serial.print("  K3B=");
    Serial.print(digitalRead(PIN_DRV_K3B) ? "ON" : "off");
    Serial.print("  K3C=");
    Serial.println(digitalRead(PIN_DRV_K3C) ? "ON" : "off");
    Serial.print("          K1=");
    Serial.print(digitalRead(PIN_DRV_K1) ? "ON" : "off");
    Serial.print("   KSP=");
    Serial.println(digitalRead(PIN_DRV_KSP) ? "ON" : "off");

    Serial.print("  Fback:  K3A=");
    Serial.print(readFeedback(PIN_FB_K3A) ? "CLOSED" : "open");
    Serial.print("  K3B=");
    Serial.print(readFeedback(PIN_FB_K3B) ? "CLOSED" : "open");
    Serial.print("  K3C=");
    Serial.println(readFeedback(PIN_FB_K3C) ? "CLOSED" : "open");
    Serial.print("          K1=");
    Serial.print(readFeedback(PIN_FB_K1) ? "CLOSED" : "open");
    Serial.print("   KSP=");
    Serial.println(readFeedback(PIN_FB_KSP) ? "CLOSED" : "open");

    Serial.print("  E-stop: ");
    Serial.println(digitalRead(PIN_ESTOP) == LOW ? "PRESSED" : "released");

    if (currentState == STATE_FAULT) {
        Serial.print("  Fault:  ");
        Serial.println(faultReason);
    }
    Serial.println("------------------------------------");
}

void runSelfTest() {
    Serial.println("SELFTEST:Starting...");

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

    // Check E-stop released
    Serial.print("  E-stop released: ");
    if (digitalRead(PIN_ESTOP) == HIGH) {
        Serial.println("PASS");
    } else {
        Serial.println("FAIL - E-stop is pressed");
        return;
    }

    // Test Phase A
    Serial.println("  Testing Phase A...");
    switchToPhaseA();
    if (currentState != STATE_PHASE_A) {
        Serial.println("SELFTEST:FAIL - Phase A switch failed");
        return;
    }
    delay(300);
    switchToOff();
    if (currentState != STATE_OFF) {
        Serial.println("SELFTEST:FAIL - OFF from Phase A failed");
        return;
    }
    delay(300);

    // Test Phase B
    Serial.println("  Testing Phase B...");
    switchToPhaseB();
    if (currentState != STATE_PHASE_B) {
        Serial.println("SELFTEST:FAIL - Phase B switch failed");
        return;
    }
    delay(300);
    switchToOff();
    if (currentState != STATE_OFF) {
        Serial.println("SELFTEST:FAIL - OFF from Phase B failed");
        return;
    }
    delay(300);

    // Test Phase C
    Serial.println("  Testing Phase C...");
    switchToPhaseC();
    if (currentState != STATE_PHASE_C) {
        Serial.println("SELFTEST:FAIL - Phase C switch failed");
        return;
    }
    delay(300);
    switchToOff();
    if (currentState != STATE_OFF) {
        Serial.println("SELFTEST:FAIL - OFF from Phase C failed");
        return;
    }
    delay(300);

    // Test FORM 3
    Serial.println("  Testing FORM 3 (all phases)...");
    switchToForm3();
    if (currentState != STATE_FORM3) {
        Serial.println("SELFTEST:FAIL - FORM 3 switch failed");
        return;
    }
    delay(300);
    switchToOff();
    if (currentState != STATE_OFF) {
        Serial.println("SELFTEST:FAIL - OFF from FORM 3 failed");
        return;
    }
    delay(300);

    // Test FORM 1
    Serial.println("  Testing FORM 1 (commoned)...");
    switchToForm1();
    if (currentState != STATE_FORM1) {
        Serial.println("SELFTEST:FAIL - FORM 1 switch failed");
        return;
    }
    delay(300);
    switchToOff();
    if (currentState != STATE_OFF) {
        Serial.println("SELFTEST:FAIL - OFF from FORM 1 failed");
        return;
    }

    Serial.println("SELFTEST:PASS - All tests passed (A, B, C, FORM3, FORM1)");
}

// =======================================================
// COMMAND PROCESSING
// =======================================================

void processCommand(char cmd) {
    switch (cmd) {
        case 'A': case 'a':
            switchToPhaseA();
            break;
        case 'B': case 'b':
            switchToPhaseB();
            break;
        case 'C': case 'c':
            switchToPhaseC();
            break;
        case '3':
            switchToForm3();
            break;
        case '1':
            switchToForm1();
            break;
        case '0':
            switchToOff();
            break;
        case 'S': case 's':
            reportStatus();
            break;
        case 'T': case 't':
            runSelfTest();
            break;
        default:
            Serial.print("UNKNOWN:");
            Serial.println(cmd);
            Serial.println("Commands:");
            Serial.println("  'A'=PhaseA  'B'=PhaseB  'C'=PhaseC");
            Serial.println("  '3'=FORM3   '1'=FORM1   '0'=OFF");
            Serial.println("  'S'=Status  'T'=SelfTest");
            break;
    }
}

// =======================================================
// LED MANAGEMENT
// =======================================================

void updateLeds() {
    switch (currentState) {
        case STATE_OFF:
            setLeds(false, false, false);
            break;
        case STATE_PHASE_A:
        case STATE_PHASE_B:
        case STATE_PHASE_C:
        case STATE_FORM3:
            setLeds(true, false, false);   // Green = any FORM 3 mode
            break;
        case STATE_FORM1:
            setLeds(false, true, false);   // Blue = FORM 1
            break;
        case STATE_SWITCHING:
            setLeds(true, true, false);    // Both during transition
            break;
        case STATE_FAULT:
            if (millis() - lastFaultBlink > LED_FAULT_BLINK_MS) {
                faultLedState = !faultLedState;
                lastFaultBlink = millis();
            }
            setLeds(false, false, faultLedState);
            break;
        case STATE_ESTOP:
            setLeds(false, false, true);   // Solid red
            break;
    }
}
